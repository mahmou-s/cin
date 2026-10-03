import uuid

import httpx
import pytest
from apps.api.app.schemas import AssertionReview


def valid_review_payload():
    return {
        "decision": "VERIFY",
        "contradiction_score": 0,
        "evidence_assessments": [
            {
                "evidence_id": str(uuid.uuid4()),
                "authority": .8,
                "directness": .8,
                "recency": .8,
                "validation": .8,
                "consistency": .8,
                "independence": .8,
                "completeness": .8,
            }
        ],
    }


def test_review_schema_rejects_missing_assessment():
    with pytest.raises(Exception):
        AssertionReview(decision="VERIFY")


def test_review_schema_rejects_empty_assessment_list():
    with pytest.raises(Exception):
        AssertionReview(decision="VERIFY", evidence_assessments=[])


def test_review_schema_rejects_out_of_range_value():
    payload = valid_review_payload()
    payload["evidence_assessments"][0]["authority"] = 1.1
    with pytest.raises(Exception):
        AssertionReview.model_validate(payload)


@pytest.mark.asyncio
async def test_review_endpoint_returns_422_for_unlinked_evidence(monkeypatch):
    pytest.importorskip("asyncpg")
    from fastapi import FastAPI
    from apps.api.app.api.v1 import routes

    app = FastAPI()
    app.include_router(routes.router, prefix="/api/v1")

    async def fake_db():
        yield object()

    async def fake_review(db, assertion_id, data, reviewer):
        raise ValueError("REVIEW_EVIDENCE_ASSESSMENTS_MUST_MATCH_ASSERTION_EVIDENCE")

    app.dependency_overrides[routes.get_db] = fake_db
    monkeypatch.setattr(routes, "review_assertion", fake_review)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/assertions/{uuid.uuid4()}/review",
            json=valid_review_payload(),
            headers={"Authorization": "Bearer demo-reviewer-key"},
        )
    assert response.status_code == 422
    assert response.json()["detail"] == "REVIEW_EVIDENCE_ASSESSMENTS_MUST_MATCH_ASSERTION_EVIDENCE"
