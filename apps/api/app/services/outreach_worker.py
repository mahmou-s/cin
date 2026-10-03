"""Periodic demonstrator worker for ADR-012 outreach reconciliation and delivery."""
from __future__ import annotations

import asyncio
import logging

from ..config import settings
from ..db import SessionLocal
from .outreach import deliver_verified_digests, run_digest_reconciliation

logger = logging.getLogger("cin.outreach")


async def demo_digest_sender(payload: dict) -> None:
    """Injectable demonstrator sender; no external email/API integration is performed."""
    logger.info(
        "outreach delivery prepared for %s: interest_count=%s display_names=%s",
        payload.get("external_entity_ref"),
        payload.get("interest_count"),
        payload.get("user_display_names"),
    )


async def run_cycle(sender=demo_digest_sender) -> tuple[int, int]:
    async with SessionLocal() as db:
        created = await run_digest_reconciliation(db)
        sent = await deliver_verified_digests(db, sender)
    return len(created), len(sent)


async def main(sender=demo_digest_sender) -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    interval = max(1, settings.outreach_reconcile_interval_seconds)
    logger.info("outreach reconcile interval=%ss", interval)
    while True:
        try:
            created, sent = await run_cycle(sender)
            logger.info("outreach reconciliation created=%d sent=%d", created, sent)
        except Exception:
            logger.exception("outreach reconciliation cycle failed")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
