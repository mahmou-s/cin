from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import (
    Evidence,
    EvidenceKind,
    OutreachDigest,
    OutreachDigestSignal,
    OutreachDigestStatus,
    OutreachSignal,
    User,
    UserProfile,
)

ContactDiscovery = Callable[[str], dict | None | Awaitable[dict | None]]
DigestSender = Callable[[dict], Awaitable[None]]
logger = logging.getLogger("cin.outreach")


async def get_or_create_user(db: AsyncSession, principal_id: str) -> User:
    user = await db.scalar(select(User).where(User.principal_id == principal_id))
    if user:
        return user
    user = User(principal_id=principal_id)
    db.add(user)
    await db.flush()
    return user


async def record_interest_signal(
    db: AsyncSession,
    user_id: UUID,
    source_content_ref: str,
    external_entity_ref: str,
) -> tuple[OutreachSignal, bool]:
    existing = await db.scalar(
        select(OutreachSignal).where(
            OutreachSignal.user_id == user_id,
            OutreachSignal.source_content_ref == source_content_ref,
        )
    )
    if existing:
        return existing, True
    signal = OutreachSignal(
        user_id=user_id,
        source_content_ref=source_content_ref,
        external_entity_ref=external_entity_ref,
    )
    db.add(signal)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(
            select(OutreachSignal).where(
                OutreachSignal.user_id == user_id,
                OutreachSignal.source_content_ref == source_content_ref,
            )
        )
        if existing is None:
            raise
        return existing, True
    await db.refresh(signal)
    return signal, False


async def discover_or_reuse_contact_channel(
    db: AsyncSession,
    external_entity_ref: str,
    discovered_channel: ContactDiscovery | dict | None = None,
) -> Evidence | None:
    existing = await db.scalar(
        select(Evidence)
        .where(
            Evidence.evidence_kind == EvidenceKind.EXTERNAL_CONTACT_CHANNEL,
            Evidence.external_entity_ref == external_entity_ref,
        )
        .order_by(Evidence.created_at.desc())
    )
    if existing:
        return existing
    if discovered_channel is None:
        return None
    if callable(discovered_channel):
        channel = discovered_channel(external_entity_ref)
        if hasattr(channel, "__await__"):
            channel = await channel
    else:
        channel = discovered_channel
    if not channel:
        return None
    evidence = Evidence(
        title=channel.get("title") or f"External contact channel: {external_entity_ref}",
        evidence_type="external_contact_channel",
        evidence_kind=EvidenceKind.EXTERNAL_CONTACT_CHANNEL,
        external_entity_ref=external_entity_ref,
        content_url=channel.get("content_url"),
        content_text=channel.get("content_text"),
        mime_type=channel.get("mime_type"),
        validation_status="PENDING",
        independence_key="__unknown_source__",
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


async def run_digest_reconciliation(db: AsyncSession, now: datetime | None = None) -> list[OutreachDigest]:
    now = now or datetime.utcnow()
    linked_signal_ids = select(OutreachDigestSignal.signal_id)
    signals = (
        await db.scalars(
            select(OutreachSignal)
            .where(~OutreachSignal.id.in_(linked_signal_ids))
            .order_by(OutreachSignal.external_entity_ref, OutreachSignal.created_at)
        )
    ).all()
    by_entity: dict[str, list[OutreachSignal]] = {}
    for signal in signals:
        by_entity.setdefault(signal.external_entity_ref, []).append(signal)

    created: list[OutreachDigest] = []
    for entity_ref, entity_signals in by_entity.items():
        latest_cooldown = await db.scalar(
            select(func.max(OutreachDigest.cooldown_until)).where(
                OutreachDigest.external_entity_ref == entity_ref
            )
        )
        if latest_cooldown and latest_cooldown > now:
            continue
        digest = OutreachDigest(
            external_entity_ref=entity_ref,
            status=OutreachDigestStatus.PENDING,
            scheduled_for=now,
            cooldown_until=now + timedelta(seconds=settings.outreach_cooldown_seconds),
        )
        db.add(digest)
        await db.flush()
        db.add_all([
            OutreachDigestSignal(digest_id=digest.id, signal_id=signal.id)
            for signal in entity_signals
        ])
        created.append(digest)
    if created:
        await db.commit()
        for digest in created:
            await db.refresh(digest)
    return created


async def deliver_verified_digests(db: AsyncSession, sender: DigestSender) -> list[UUID]:
    digests = (
        await db.scalars(
            select(OutreachDigest)
            .where(OutreachDigest.status == OutreachDigestStatus.PENDING)
            .order_by(OutreachDigest.scheduled_for, OutreachDigest.created_at)
        )
    ).all()
    sent: list[UUID] = []
    for digest in digests:
        channel = await db.scalar(
            select(Evidence)
            .where(
                Evidence.evidence_kind == EvidenceKind.EXTERNAL_CONTACT_CHANNEL,
                Evidence.external_entity_ref == digest.external_entity_ref,
                Evidence.validation_status == "VERIFIED",
            )
            .order_by(Evidence.created_at.desc())
        )
        if channel is None:
            continue
        signal_rows = (
            await db.scalars(
                select(OutreachSignal)
                .join(OutreachDigestSignal, OutreachDigestSignal.signal_id == OutreachSignal.id)
                .where(OutreachDigestSignal.digest_id == digest.id)
                .order_by(OutreachSignal.created_at)
            )
        ).all()
        user_ids = [s.user_id for s in signal_rows]
        users = (
            await db.scalars(select(User).where(User.id.in_(user_ids)))
        ).all()
        principal_by_id = {user.id: user.principal_id for user in users}
        profiles = (
            await db.scalars(
                select(UserProfile).where(
                    UserProfile.principal_id.in_([user.principal_id for user in users])
                )
            )
        ).all()
        display_name_by_principal = {profile.principal_id: profile.display_name for profile in profiles}
        user_principal_ids = [principal_by_id[user_id] for user_id in user_ids]
        user_display_names = [
            display_name_by_principal.get(principal_id) or principal_id
            for principal_id in user_principal_ids
        ]

        # Keep principal IDs available for internal audit/debugging only. They are
        # deliberately excluded from the payload crossing the sender boundary.
        audit_principal_ids = list(user_principal_ids)
        logger.debug("outreach delivery audit principals=%s digest=%s", audit_principal_ids, digest.id)
        payload = {
            "external_entity_ref": digest.external_entity_ref,
            "channel": channel.content_url or channel.content_text,
            "interest_count": len(signal_rows),
            "user_display_names": user_display_names,
            "source_content_refs": [s.source_content_ref for s in signal_rows],
        }
        try:
            await sender(payload)
        except Exception:
            digest.status = OutreachDigestStatus.FAILED
            await db.commit()
            continue
        digest.status = OutreachDigestStatus.SENT
        digest.sent_at = datetime.utcnow()
        await db.commit()
        sent.append(digest.id)
    return sent
