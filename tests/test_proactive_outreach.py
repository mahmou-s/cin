import os
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.integration


@pytest.fixture
async def db_available():
    try:
        from apps.api.app.db import SessionLocal
        async with SessionLocal() as db:
            await db.execute(select(1))
    except Exception as exc:
        pytest.skip(f"PostgreSQL unavailable: {type(exc).__name__}")


@pytest.fixture
def sender_spy():
    calls = []

    async def sender(payload):
        calls.append(payload)

    return calls, sender


@pytest.mark.asyncio
async def test_duplicate_signal_is_idempotent(db_available):
    from apps.api.app.db import SessionLocal
    from apps.api.app.services.outreach import get_or_create_user, record_interest_signal
    from apps.api.app.models import OutreachSignal

    principal = f"outreach-idempotency-{uuid.uuid4()}"
    async with SessionLocal() as db:
        user = await get_or_create_user(db, principal)
        first, first_idempotent = await record_interest_signal(db, user.id, "video:001", "company:001")
        second, second_idempotent = await record_interest_signal(db, user.id, "video:001", "company:001")
        rows = (await db.scalars(select(OutreachSignal).where(OutreachSignal.user_id == user.id, OutreachSignal.source_content_ref == "video:001"))).all()
    assert first_idempotent is False
    assert second_idempotent is True
    assert first.id == second.id
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_reconciliation_respects_cooldown(db_available):
    from apps.api.app.db import SessionLocal
    from apps.api.app.services.outreach import get_or_create_user, record_interest_signal, run_digest_reconciliation
    from apps.api.app.models import OutreachDigest, OutreachDigestStatus

    principal = f"outreach-cooldown-{uuid.uuid4()}"
    entity = f"company:{uuid.uuid4()}"
    async with SessionLocal() as db:
        user = await get_or_create_user(db, principal)
        signal, _ = await record_interest_signal(db, user.id, "video:cooldown", entity)
        now = datetime.utcnow()
        existing = OutreachDigest(external_entity_ref=entity, status=OutreachDigestStatus.PENDING, scheduled_for=now, cooldown_until=now + timedelta(hours=1))
        db.add(existing)
        await db.commit()
        created = await run_digest_reconciliation(db, now=now)
    assert created == []


@pytest.mark.asyncio
async def test_pending_channel_never_sends(db_available, sender_spy):
    from apps.api.app.db import SessionLocal
    from apps.api.app.services.outreach import get_or_create_user, record_interest_signal, run_digest_reconciliation, deliver_verified_digests, discover_or_reuse_contact_channel

    calls, sender = sender_spy
    principal = f"outreach-pending-{uuid.uuid4()}"
    entity = f"company:{uuid.uuid4()}"
    async with SessionLocal() as db:
        user = await get_or_create_user(db, principal)
        await record_interest_signal(db, user.id, "video:pending", entity)
        channel = await discover_or_reuse_contact_channel(db, entity, {"content_url": "https://example.test/contact"})
        assert channel.validation_status == "PENDING"
        await run_digest_reconciliation(db)
        sent = await deliver_verified_digests(db, sender)
    assert sent == []
    assert calls == []


@pytest.mark.asyncio
async def test_verified_channel_sends_and_marks_digest_sent(db_available, sender_spy):
    from apps.api.app.db import SessionLocal
    from apps.api.app.services.outreach import get_or_create_user, record_interest_signal, run_digest_reconciliation, deliver_verified_digests, discover_or_reuse_contact_channel
    from apps.api.app.models import OutreachDigest, OutreachDigestStatus, UserProfile

    calls, sender = sender_spy
    principal = f"outreach-verified-{uuid.uuid4()}"
    entity = f"company:{uuid.uuid4()}"
    async with SessionLocal() as db:
        user = await get_or_create_user(db, principal)
        db.add(UserProfile(principal_id=principal, display_name="Verified User"))
        await db.commit()
        await record_interest_signal(db, user.id, "video:verified", entity)
        channel = await discover_or_reuse_contact_channel(db, entity, {"content_url": "https://example.test/contact"})
        channel.validation_status = "VERIFIED"
        await db.commit()
        created = await run_digest_reconciliation(db)
        assert len(created) == 1
        sent = await deliver_verified_digests(db, sender)
        digest = await db.get(OutreachDigest, created[0].id)
    assert sent == [created[0].id]
    assert len(calls) == 1
    assert calls[0]["user_display_names"] == ["Verified User"]
    assert "user_principal_ids" not in calls[0]
    assert digest.status == OutreachDigestStatus.SENT


@pytest.mark.asyncio
async def test_full_integration_signal_digest_verify_deliver(db_available, sender_spy):
    from apps.api.app.db import SessionLocal
    from apps.api.app.services.outreach import get_or_create_user, record_interest_signal, run_digest_reconciliation, deliver_verified_digests, discover_or_reuse_contact_channel
    from apps.api.app.models import OutreachDigestStatus

    calls, sender = sender_spy
    principal = f"outreach-full-{uuid.uuid4()}"
    entity = f"company:{uuid.uuid4()}"
    async with SessionLocal() as db:
        user = await get_or_create_user(db, principal)
        signal, idempotent = await record_interest_signal(db, user.id, "video:full", entity)
        assert idempotent is False
        digest_list = await run_digest_reconciliation(db)
        assert len(digest_list) == 1
        assert digest_list[0].status == OutreachDigestStatus.PENDING
        channel = await discover_or_reuse_contact_channel(db, entity, {"content_url": "https://example.test/contact"})
        assert channel.validation_status == "PENDING"
        assert await deliver_verified_digests(db, sender) == []
        assert calls == []
        channel.validation_status = "VERIFIED"
        await db.commit()
        sent = await deliver_verified_digests(db, sender)
        assert sent == [digest_list[0].id]
    assert len(calls) == 1
    assert calls[0]["external_entity_ref"] == entity
    assert calls[0]["user_display_names"] == [principal]
    assert "user_principal_ids" not in calls[0]
