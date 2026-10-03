from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import Principal, require_steward, require_submitter
from ...db import get_db
from ...schemas import OutreachSignalCreate, OutreachSignalOut
from ...services.outreach import get_or_create_user, record_interest_signal
from ...services.outreach_worker import demo_digest_sender

router = APIRouter()


@router.post("/outreach/signal", response_model=OutreachSignalOut)
async def signal_interest(
    data: OutreachSignalCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_submitter),
):
    # This endpoint represents an explicit user opt-in action. Viewing content alone
    # never calls this service and cannot create an outreach signal.
    user = await get_or_create_user(db, principal.subject)
    signal, idempotent = await record_interest_signal(
        db,
        user.id,
        data.source_content_ref,
        data.external_entity_ref,
    )
    return OutreachSignalOut(
        id=signal.id,
        source_content_ref=signal.source_content_ref,
        external_entity_ref=signal.external_entity_ref,
        created_at=signal.created_at,
        idempotent=idempotent,
    )


@router.post("/outreach/reconcile")
async def reconcile_outreach(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_steward),
):
    from ...services.outreach import deliver_verified_digests, run_digest_reconciliation

    created = await run_digest_reconciliation(db)
    sent = await deliver_verified_digests(db, demo_digest_sender)
    return {"digests_created": len(created), "digests_sent": len(sent)}
