"""Redis-driven transactional-outbox projector with periodic reconciliation.

PostgreSQL remains the source of truth. Redis carries event IDs. Neo4j is an
idempotent projection and can be rebuilt from verified facts.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta

from neo4j import AsyncGraphDatabase
from redis.asyncio import Redis
from sqlalchemy import select

from ..config import settings
from ..db import SessionLocal
from ..models import SyncEvent
from .redis_queue import QUEUE_KEY, redis_client

logger = logging.getLogger("cin.outbox")
MAX_ATTEMPTS = 10

CYPHER = """
MERGE (c:Community {id:$community_id})
SET c.name=$community_name, c.updated_at=datetime()
MERGE (a:CapabilityAssertion {id:$assertion_id})
SET a.confidence_score=$confidence_score,
    a.confidence_level=$confidence_level,
    a.status='VERIFIED',
    a.updated_at=datetime()
MERGE (t:CapabilityType {id:$capability_type_id})
SET t.code=$capability_code, t.name=$capability_name
MERGE (c)-[:HAS_CAPABILITY]->(a)
MERGE (a)-[:INSTANCE_OF]->(t)
"""


async def reconcile_stale_events(redis: Redis, now: datetime | None = None) -> int:
    """Re-enqueue recoverable PENDING and timed-out PROCESSING events."""
    now = now or datetime.utcnow()
    pending_cutoff = now - timedelta(seconds=settings.outbox_reconcile_interval_seconds)
    processing_cutoff = now - timedelta(seconds=settings.processing_timeout_seconds)
    async with SessionLocal() as db:
        rows = (await db.scalars(
            select(SyncEvent)
            .where(
                SyncEvent.attempts < MAX_ATTEMPTS,
                (((SyncEvent.status == "PENDING") & (SyncEvent.created_at <= pending_cutoff) & ((SyncEvent.next_attempt_at == None) | (SyncEvent.next_attempt_at <= now)))
                    | ((SyncEvent.status == "PROCESSING") & (SyncEvent.processing_started_at <= processing_cutoff))),
            )
            .order_by(SyncEvent.created_at)
            .limit(500)
            .with_for_update(skip_locked=True)
        )).all()
        event_ids = []
        for event in rows:
            if event.status == "PROCESSING":
                event.status = "PENDING"
                event.last_error = "PROCESSING_TIMEOUT_RECOVERED"
            event_ids.append(str(event.id))
        await db.commit()
    for event_id in event_ids:
        await redis.rpush(QUEUE_KEY, json.dumps({"event_id": event_id}, separators=(",", ":")))
    if event_ids:
        logger.info("reconciled %d outbox events", len(event_ids))
    return len(event_ids)


async def recover_pending(redis: Redis) -> int:
    """Backward-compatible startup reconciliation entry point."""
    return await reconcile_stale_events(redis, datetime.utcnow() + timedelta(seconds=settings.outbox_reconcile_interval_seconds))


async def mark_processing(db, event_id):
    async with db.begin():
        event = await db.scalar(select(SyncEvent).where(SyncEvent.id == event_id).with_for_update())
        if not event or event.status != "PENDING":
            return None
        if event.attempts >= MAX_ATTEMPTS:
            event.status = "DEAD_LETTER"
            return None
        event.status = "PROCESSING"
        event.processing_started_at = datetime.utcnow()
        event.attempts += 1
        return event.payload


async def finalize(event_id, success: bool, error: str | None = None):
    async with SessionLocal() as db:
        async with db.begin():
            event = await db.get(SyncEvent, event_id, with_for_update=True)
            if not event:
                return
            if success:
                event.status = "PROCESSED"
                event.processed_at = datetime.utcnow()
                event.processing_started_at = None
                event.last_error = None
            else:
                event.status = "PENDING" if event.attempts < MAX_ATTEMPTS else "DEAD_LETTER"
                event.processing_started_at = None
                event.next_attempt_at = datetime.utcnow() + timedelta(seconds=min(300, settings.outbox_backoff_base_seconds * (2 ** max(0, event.attempts - 1)))) if event.status == "PENDING" else None
                event.last_error = (error or "unknown error")[:4000]


async def process_event(driver, event_id: str):
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError:
        logger.error("invalid event id: %s", event_id)
        return

    async with SessionLocal() as db:
        payload = await mark_processing(db, event_uuid)
    if not payload:
        return

    try:
        async with driver.session() as session:
            await session.execute_write(lambda tx: tx.run(CYPHER, **payload))
        await finalize(event_uuid, True)
        logger.info("projected outbox event %s", event_id)
    except Exception as exc:
        logger.exception("projection failed for %s", event_id)
        await finalize(event_uuid, False, str(exc))


async def main():
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    redis = redis_client()
    driver = AsyncGraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        await driver.verify_connectivity()
        last_reconcile = datetime.utcnow() - timedelta(seconds=settings.outbox_reconcile_interval_seconds)
        logger.info("outbox reconcile interval=%ss processing timeout=%ss", settings.outbox_reconcile_interval_seconds, settings.processing_timeout_seconds)
        while True:
            now = datetime.utcnow()
            if (now - last_reconcile).total_seconds() >= settings.outbox_reconcile_interval_seconds:
                await reconcile_stale_events(redis, now)
                last_reconcile = now
            item = await redis.blpop(QUEUE_KEY, timeout=1)
            if item:
                _, raw = item
                try:
                    event_id = json.loads(raw)["event_id"]
                    await process_event(driver, event_id)
                except Exception:
                    logger.exception("invalid queue message: %r", raw)
    finally:
        await driver.close()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
