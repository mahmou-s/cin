from fastapi import APIRouter, Depends, HTTPException
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...db import get_db
from ...models import CapabilityType, CapabilityAssertion, Community, AssertionEvidence, Evidence
from ...schemas import AssertionSubmit, AssertionOut, CapabilityOut, AssertionReview, PendingAssertionOut
from ...services.assertions import submit_assertion, review_assertion
from ...services.redis_queue import enqueue_event
from ...services.confidence import derive_independence_key
from ...auth import Principal, require_submitter, require_reviewer

router = APIRouter()


async def _evidence_ids(db: AsyncSession, assertion_id):
    return list(await db.scalars(
        select(AssertionEvidence.evidence_id)
        .where(AssertionEvidence.assertion_id == assertion_id)
        .order_by(AssertionEvidence.evidence_id)
    ))


@router.get("/capabilities", response_model=list[CapabilityOut])
async def capabilities(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(CapabilityType).order_by(CapabilityType.code))).all()


@router.post("/assertions/submit", response_model=AssertionOut)
async def assertions_submit(data: AssertionSubmit, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    try:
        assertion = await submit_assertion(db, data, principal.subject)
        return AssertionOut(
            id=assertion.id,
            evidence_ids=await _evidence_ids(db, assertion.id),
            confidence_score=assertion.confidence_score,
            confidence_raw_score=assertion.confidence_raw_score,
            confidence_gate_reasons=assertion.confidence_gate_reasons,
            confidence_level=assertion.confidence_level,
            status=assertion.status,
            conflict_flag=assertion.conflict_flag,
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(404, str(e))
    except Exception:
        await db.rollback()
        raise HTTPException(500, "ASSERTION_SUBMISSION_FAILED")


@router.get("/assertions/pending", response_model=list[PendingAssertionOut])
async def pending_assertions(db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_reviewer)):
    rows = await db.execute(
        select(CapabilityAssertion, Community.name, CapabilityType.code, CapabilityType.name)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .where(CapabilityAssertion.status.in_(["SUBMITTED", "CONFLICT"]))
        .order_by(CapabilityAssertion.created_at)
    )
    result = []
    for a, community, code, name in rows.all():
        result.append(PendingAssertionOut(
            id=a.id,
            evidence_ids=await _evidence_ids(db, a.id),
            evidence=[{"id": e.id, "derived_independence_key": derive_independence_key(e.__dict__), "canonical_independence_key": "__unknown_source__"} for e in (await db.execute(select(Evidence).join(AssertionEvidence, AssertionEvidence.evidence_id == Evidence.id).where(AssertionEvidence.assertion_id == a.id))).scalars().all()],
            community_name=community,
            capability_code=code,
            capability_name=name,
            confidence_score=a.confidence_score,
            confidence_raw_score=a.confidence_raw_score,
            confidence_gate_reasons=a.confidence_gate_reasons,
            confidence_level=a.confidence_level,
            status=a.status,
            created_at=a.created_at.isoformat(),
        ))
    return result


@router.post("/assertions/{assertion_id}/review", response_model=AssertionOut)
async def review(assertion_id, data: AssertionReview, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_reviewer)):
    try:
        assertion, event = await review_assertion(db, assertion_id, data, principal.subject)
        enqueue_status = None
        if event:
            enqueue_status = event.status
            try:
                await enqueue_event(str(event.id))
            except RedisError as exc:
                # PostgreSQL transaction already committed. The durable outbox
                # remains PENDING and the worker reconcile sweep will recover it.
                import logging
                logging.getLogger("cin.api").warning("Redis enqueue failed after commit; event remains PENDING: %s", event.id)
                enqueue_status = "PENDING"
        return AssertionOut(
            id=assertion.id,
            evidence_ids=await _evidence_ids(db, assertion.id),
            confidence_score=assertion.confidence_score,
            confidence_raw_score=assertion.confidence_raw_score,
            confidence_gate_reasons=assertion.confidence_gate_reasons,
            confidence_level=assertion.confidence_level,
            status=assertion.status,
            conflict_flag=assertion.conflict_flag,
            outbox_event_id=event.id if event else None,
            outbox_status=enqueue_status,
        )
    except ValueError as e:
        await db.rollback()
        detail = str(e)
        status = 422 if detail in {"REVIEW_EVIDENCE_ASSESSMENTS_MUST_MATCH_ASSERTION_EVIDENCE", "SELF_REVIEW_FORBIDDEN"} else 404
        raise HTTPException(status, detail)
    except Exception:
        await db.rollback()
        raise HTTPException(500, "ASSERTION_REVIEW_FAILED")
