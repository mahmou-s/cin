from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import (
    Community,
    CapabilityType,
    CapabilityAssertion,
    Evidence,
    AssertionEvidence,
    EvidenceAssessment,
    ValidationEvent,
    SyncEvent,
)
from ..schemas import AssertionSubmit, AssertionReview
from .confidence import calculate_confidence, calculate_confidence_details, derive_independence_key

CONFIDENCE_DIMENSIONS = (
    "authority", "directness", "recency", "validation",
    "consistency", "independence", "completeness",
)


def _dimensions(item) -> dict:
    return {key: float(getattr(item, key) if hasattr(item, key) else item[key]) for key in CONFIDENCE_DIMENSIONS}


async def submit_assertion(db: AsyncSession, data: AssertionSubmit, submitter: str = "unknown-submitters"):
    ct = await db.scalar(select(CapabilityType).where(CapabilityType.id == data.capability_type_id))
    if not ct:
        raise ValueError("CAPABILITY_TYPE_NOT_FOUND")
    community = await db.scalar(
        select(Community).where(
            Community.name == data.community.name,
            Community.country_code == data.community.country_code,
        )
    )
    if not community:
        community = Community(**data.community.model_dump())
        db.add(community)
        await db.flush()

    ev_models = []
    claimed = []
    for item in data.evidence:
        values = item.model_dump()
        # The submitter cannot establish canonical independence. Derive the
        # source group server-side from URL host, then SHA-256, else shared
        # unknown-source group.
        values["independence_key"] = derive_independence_key(values)
        em = Evidence(**values)
        db.add(em)
        await db.flush()
        ev_models.append(em)
        claimed.append({
            "evidence_id": str(em.id),
            **_dimensions(values),
            "derived_independence_key": em.independence_key,
        })

    claimed_score, claimed_level, claimed_raw_score, claimed_gate_reasons = calculate_confidence_details(claimed)
    assertion = CapabilityAssertion(
        community_id=community.id,
        capability_type_id=ct.id,
        scope=data.scope,
        scale=data.scale,
        quantity=data.quantity,
        unit=data.unit,
        measurement_period=data.measurement_period,
        maturity_level=data.maturity_level,
        status="SUBMITTED",
        confidence_score=0.0,
        confidence_level="UNVERIFIED",
        conflict_flag=False,
        confidence_raw_score=0.0,
        confidence_gate_reasons={"canonical": False},
        submitted_by=submitter,
    )
    db.add(assertion)
    await db.flush()
    for evidence in ev_models:
        db.add(AssertionEvidence(assertion_id=assertion.id, evidence_id=evidence.id))
    db.add(ValidationEvent(
        assertion_id=assertion.id,
        event_type="AUTO_ASSESSMENT",
        actor="system",
        details={
            "canonical": False,
            "confidence": 0.0,
            "level": "UNVERIFIED",
            "claimed_confidence": claimed_score,
            "claimed_raw_score": claimed_raw_score,
            "claimed_gate_reasons": claimed_gate_reasons,
            "claimed_level": claimed_level,
            "claimed_evidence": claimed,
        },
    ))
    await db.commit()
    return assertion


async def review_assertion(db: AsyncSession, assertion_id, data: AssertionReview, reviewer: str):
    assertion = await db.scalar(
        select(CapabilityAssertion)
        .where(CapabilityAssertion.id == assertion_id)
        .with_for_update()
    )
    if not assertion:
        raise ValueError("ASSERTION_NOT_FOUND")
    if assertion.status not in {"SUBMITTED", "CONFLICT"}:
        raise ValueError("ASSERTION_NOT_REVIEWABLE")
    if assertion.submitted_by and assertion.submitted_by == reviewer:
        raise ValueError("SELF_REVIEW_FORBIDDEN")

    evidence_rows = await _evidence_models(db, assertion.id)
    expected_ids = {str(item.id) for item in evidence_rows}
    supplied_ids = {str(item.evidence_id) for item in data.evidence_assessments}
    if supplied_ids != expected_ids or len(supplied_ids) != len(data.evidence_assessments):
        raise ValueError("REVIEW_EVIDENCE_ASSESSMENTS_MUST_MATCH_ASSERTION_EVIDENCE")

    claimed = []
    reviewed = []
    review_by_id = {str(item.evidence_id): item.model_dump() for item in data.evidence_assessments}
    for evidence in evidence_rows:
        assessment = review_by_id[str(evidence.id)]
        canonical_key = (assessment.get("independence_key") or "__unknown_source__").strip()
        if not assessment.get("independence_key") and assessment.get("confirm_derived_independence"):
            canonical_key = (evidence.independence_key or "__unknown_source__").strip()
        elif not assessment.get("independence_key"):
            canonical_key = "__unknown_source__"
        claimed_item = {
            "evidence_id": str(evidence.id),
            **_dimensions(evidence),
            "independence_key": evidence.independence_key,
        }
        reviewed_item = {
            "evidence_id": str(evidence.id),
            **_dimensions(assessment),
            "independence_key": canonical_key,
        }
        claimed.append(claimed_item)
        reviewed.append(reviewed_item)
        db.add(EvidenceAssessment(
            assertion_id=assertion.id,
            evidence_id=evidence.id,
            reviewer=reviewer,
            **_dimensions(assessment),
            independence_key=canonical_key,
        ))

    new_score, new_level, raw_score, gate_reasons = calculate_confidence_details(reviewed, data.contradiction_score)
    assertion.confidence_score = new_score
    assertion.confidence_raw_score = raw_score
    assertion.confidence_gate_reasons = gate_reasons
    assertion.confidence_level = new_level
    assertion.review_note = data.note
    assertion.reviewed_at = datetime.utcnow()
    assertion.reviewed_by = reviewer
    assertion.conflict_flag = data.decision == "CONFLICT" or data.contradiction_score > .30
    assertion.status = {"VERIFY": "VERIFIED", "REJECT": "REJECTED", "CONFLICT": "CONFLICT"}[data.decision]
    db.add(ValidationEvent(
        assertion_id=assertion.id,
        event_type=f"HUMAN_{data.decision}",
        actor=reviewer,
        details={
            "note": data.note,
            "contradiction_score": data.contradiction_score,
            "confidence": new_score,
            "raw_confidence": raw_score,
            "confidence_gate_reasons": gate_reasons,
            "confidence_level": new_level,
            "claimed_evidence": claimed,
            "reviewer_evidence": reviewed,
            "reviewer_values_are_canonical": True,
        },
    ))
    event = None
    if assertion.status == "VERIFIED":
        ct = await db.scalar(select(CapabilityType).where(CapabilityType.id == assertion.capability_type_id))
        community = await db.scalar(select(Community).where(Community.id == assertion.community_id))
        payload = {
            "assertion_id": str(assertion.id),
            "community_id": str(community.id),
            "community_name": community.name,
            "capability_type_id": str(ct.id),
            "capability_code": ct.code,
            "capability_name": ct.name,
            "confidence_score": new_score,
            "confidence_level": new_level,
        }
        event = SyncEvent(
            aggregate_type="CapabilityAssertion",
            aggregate_id=assertion.id,
            event_type="ASSERTION_VERIFIED",
            payload=payload,
        )
        db.add(event)
    await db.commit()
    return assertion, event


async def _evidence_models(db: AsyncSession, assertion_id):
    rows = await db.execute(
        select(Evidence)
        .join(AssertionEvidence, AssertionEvidence.evidence_id == Evidence.id)
        .where(AssertionEvidence.assertion_id == assertion_id)
    )
    return list(rows.scalars().all())
