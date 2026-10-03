import os
import uuid
from datetime import datetime, timedelta

import httpx
import pytest
pytest.importorskip("fakeredis")
from fakeredis.aioredis import FakeRedis
from sqlalchemy import select

from apps.api.app.auth import require_reviewer, require_submitter
from apps.api.app.db import SessionLocal
from apps.api.app.models import CapabilityAssertion, CapabilityType, Community, Evidence, AssertionEvidence, EvidenceAssessment, SyncEvent
from apps.api.app.api.v1 import routes
from apps.api.app.services.assertions import submit_assertion
from apps.api.app.services.civilizational_opportunities import discover
from apps.api.app.services.outbox_worker import mark_processing, reconcile_stale_events
from apps.api.app.schemas import AssertionSubmit

pytestmark = pytest.mark.integration

TOKENS = {
    "submitter": {"Authorization": "Bearer demo-submitter-key"},
    "reviewer": {"Authorization": "Bearer demo-reviewer-key"},
    "steward": {"Authorization": "Bearer demo-steward-key"},
}


def evidence_payload(title="CI evidence", url="https://source-a.example/report"):
    return {
        "title": title,
        "evidence_type": "document",
        "content_text": "CI behavioral test evidence",
        "content_url": url,
        "authority": 0.9,
        "directness": 0.9,
        "recency": 0.9,
        "validation": 0.9,
        "consistency": 0.9,
        "independence": 0.9,
        "completeness": 0.9,
    }


async def make_assertion(client, token="demo-submitter-key", code="C01", community_name=None):
    async with SessionLocal() as db:
        ct = await db.scalar(select(CapabilityType).where(CapabilityType.code == code))
        if not ct:
            ct = CapabilityType(code=code, domain="CI", name=f"CI {code}")
            db.add(ct)
            await db.flush()
    payload = {
        "community": {"name": community_name or f"CI Community {uuid.uuid4()}", "country_code": "CI", "location": "CI"},
        "capability_type_id": str(ct.id),
        "scope": "integration-test",
        "maturity_level": "ESTABLISHED",
        "evidence": [evidence_payload()],
    }
    r = await client.post("/api/v1/assertions/submit", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
async def app_client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(routes.router, prefix="/api/v1")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_review_endpoint_422_missing_assessment(app_client):
    assertion = await make_assertion(app_client)
    r = await app_client.post(f"/api/v1/assertions/{assertion['id']}/review", json={"decision": "VERIFY", "evidence_assessments": []}, headers=TOKENS["reviewer"])
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_review_endpoint_422_unlinked_evidence(app_client):
    assertion = await make_assertion(app_client)
    payload = {"decision": "VERIFY", "evidence_assessments": [{**evidence_payload(), "evidence_id": str(uuid.uuid4())}]}
    r = await app_client.post(f"/api/v1/assertions/{assertion['id']}/review", json=payload, headers=TOKENS["reviewer"])
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_review_endpoint_422_out_of_range_value(app_client):
    assertion = await make_assertion(app_client)
    payload = {"decision": "VERIFY", "evidence_assessments": [{"evidence_id": assertion["evidence_ids"][0], "authority": 1.1, "directness": .8, "recency": .8, "validation": .8, "consistency": .8, "independence": .8, "completeness": .8}]}
    r = await app_client.post(f"/api/v1/assertions/{assertion['id']}/review", json=payload, headers=TOKENS["reviewer"])
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_review_creates_assessment_and_outbox_in_committed_transaction(app_client):
    assertion = await make_assertion(app_client)
    payload = {"decision": "VERIFY", "evidence_assessments": [{"evidence_id": assertion["evidence_ids"][0], "authority": .9, "directness": .9, "recency": .9, "validation": .9, "consistency": .9, "independence": .9, "completeness": .9}]}
    r = await app_client.post(f"/api/v1/assertions/{assertion['id']}/review", json=payload, headers=TOKENS["reviewer"])
    assert r.status_code == 200, r.text
    async with SessionLocal() as db:
        assessment = await db.scalar(select(EvidenceAssessment).where(EvidenceAssessment.assertion_id == uuid.UUID(assertion["id"])))
        outbox = await db.scalar(select(SyncEvent).where(SyncEvent.aggregate_id == uuid.UUID(assertion["id"])))
    assert assessment is not None
    assert outbox is not None and outbox.status == "PENDING"


@pytest.mark.asyncio
async def test_redis_down_review_returns_success_and_pending(monkeypatch, app_client):
    assertion = await make_assertion(app_client)
    async def redis_down(_event_id):
        from redis.exceptions import RedisError
        raise RedisError("redis unavailable")
    monkeypatch.setattr(routes, "enqueue_event", redis_down)
    payload = {"decision": "VERIFY", "evidence_assessments": [{"evidence_id": assertion["evidence_ids"][0], "authority": .9, "directness": .9, "recency": .9, "validation": .9, "consistency": .9, "independence": .9, "completeness": .9}]}
    r = await app_client.post(f"/api/v1/assertions/{assertion['id']}/review", json=payload, headers=TOKENS["reviewer"])
    assert r.status_code == 200, r.text
    assert r.json()["outbox_status"] == "PENDING"


@pytest.mark.asyncio
async def test_self_review_forbidden(app_client):
    assertion = await make_assertion(app_client, token="demo-reviewer-key")
    payload = {"decision": "VERIFY", "evidence_assessments": [{"evidence_id": assertion["evidence_ids"][0], "authority": .9, "directness": .9, "recency": .9, "validation": .9, "consistency": .9, "independence": .9, "completeness": .9}]}
    r = await app_client.post(f"/api/v1/assertions/{assertion['id']}/review", json=payload, headers=TOKENS["reviewer"])
    assert r.status_code == 422
    assert r.json()["detail"] == "SELF_REVIEW_FORBIDDEN"


@pytest.mark.asyncio
async def test_reconcile_sweep_recovers_pending_and_timed_out_processing():
    redis = FakeRedis(decode_responses=True)
    old = datetime.utcnow() - timedelta(seconds=3600)
    async with SessionLocal() as db:
        pending = SyncEvent(aggregate_type="Test", aggregate_id=uuid.uuid4(), event_type="TEST", payload={"x": 1}, status="PENDING", created_at=old)
        processing = SyncEvent(aggregate_type="Test", aggregate_id=uuid.uuid4(), event_type="TEST", payload={"x": 2}, status="PROCESSING", created_at=old, processing_started_at=old)
        db.add_all([pending, processing])
        await db.commit()
    count = await reconcile_stale_events(redis)
    assert count >= 2
    assert await redis.llen("cin:outbox:events") >= 2
    await redis.aclose()


@pytest.mark.asyncio
async def test_duplicate_delivery_is_guarded_by_status():
    event_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(SyncEvent( id=event_id, aggregate_type="Test", aggregate_id=uuid.uuid4(), event_type="TEST", payload={"x": 1}, status="PENDING"))
        await db.commit()
    async with SessionLocal() as db:
        first = await mark_processing(db, event_id)
    async with SessionLocal() as db:
        second = await mark_processing(db, event_id)
    assert first == {"x": 1}
    assert second is None


@pytest.mark.asyncio
async def test_worker_crash_mid_processing_is_recovered_by_sweep():
    event_id = uuid.uuid4()
    async with SessionLocal() as db:
        db.add(SyncEvent(id=event_id, aggregate_type="Test", aggregate_id=uuid.uuid4(), event_type="TEST", payload={"x": 3}, status="PENDING"))
        await db.commit()
    async with SessionLocal() as db:
        payload = await mark_processing(db, event_id)
    assert payload == {"x": 3}
    async with SessionLocal() as db:
        event = await db.get(SyncEvent, event_id)
        event.processing_started_at = datetime.utcnow() - timedelta(seconds=3600)
        await db.commit()
    redis = FakeRedis(decode_responses=True)
    count = await reconcile_stale_events(redis)
    assert count >= 1
    async with SessionLocal() as db:
        event = await db.get(SyncEvent, event_id)
        assert event.status == "PENDING"
    await redis.aclose()


@pytest.mark.asyncio
async def test_opportunity_discovery_includes_demo_chain_when_seeded_records_exist():
    async with SessionLocal() as db:
        community_ids = []
        for code in ["C01", "C10", "C06", "C02"]:
            ct = await db.scalar(select(CapabilityType).where(CapabilityType.code == code))
            if not ct:
                ct = CapabilityType(code=code, domain="CI", name=f"CI {code}")
                db.add(ct)
                await db.flush()
            community = Community(name=f"Demo chain {code} {uuid.uuid4()}", country_code="CI", location="CI")
            db.add(community)
            await db.flush()
            assertion = CapabilityAssertion(community_id=community.id, capability_type_id=ct.id, maturity_level="ESTABLISHED", status="VERIFIED", confidence_score=.9, confidence_raw_score=.9, confidence_gate_reasons={"high_gate_satisfied": True}, conflict_flag=False, submitted_by="demo-seed")
            db.add(assertion)
            await db.flush()
            ev = Evidence(title=f"Demo evidence {code}", content_url=f"https://source-{code}.example", authority=.9, directness=.9, recency=.9, validation=.9, consistency=.9, independence=.9, completeness=.9, independence_key=f"host:source-{code}.example")
            db.add(ev)
            await db.flush()
            db.add(AssertionEvidence(assertion_id=assertion.id, evidence_id=ev.id))
        await db.commit()
        results = await discover(db, limit=100)
    assert any(item["capability_chain"] == ["C01", "C10", "C06", "C02"] for item in results)
