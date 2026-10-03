"""Evidence-grounded investment opportunity exploration.

The explorer treats verified Products as the primary unit. Profiles are contextual
metadata only; they are not sufficient to create an opportunity. Each POTENTIAL
result is persisted as an Opportunity so it can enter the human review gate later.
The explorer is deterministic and traceable; it does not make investment decisions.
"""
from itertools import combinations
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    Product, UserProfile, CapabilityAssertion, InvestmentSupportRequest,
    Opportunity, OpportunityProduct, OpportunityAssertion, ReasoningRun,
)
from .product_opportunity_discovery import COMPLEMENT_PATTERNS


def _verified_evidence(product):
    return [e for e in product.evidences if e.validation_status == "VERIFIED"]


def _verified_assertions(product):
    return [a for a in product.capability_assertions if a.status == "VERIFIED"]


def _product_confidence(product):
    values = [float(a.confidence_score or 0) for a in _verified_assertions(product)]
    if not values:
        return 0.0
    return min(values)


def _need_signals(product):
    signals = []
    if product.goal:
        signals.append({"type": "PRODUCT_GOAL", "text": product.goal})
    for request in product.investment_requests:
        if request.status == "VERIFIED":
            signals.append({
                "type": "SUPPORT_REQUEST",
                "request_type": request.request_type,
                "goal": request.goal,
                "requested_amount": request.requested_amount,
                "currency": request.currency,
                "details": request.details,
                "source_id": str(request.id),
            })
    return signals


def _capacity(product):
    c = product.production_capacity
    if not c:
        return None
    return {
        "quantity": c.quantity,
        "unit": c.unit,
        "quality_description": c.quality_description,
        "commitment_volume": c.commitment_volume,
        "commitment_unit": c.commitment_unit,
        "delivery_days": c.delivery_days,
        "delivery_term": c.delivery_term,
        "measurement_period": c.measurement_period,
    }


def _candidate(a, b):
    if a.profile_id == b.profile_id:
        return None
    ea, eb = _verified_evidence(a), _verified_evidence(b)
    aa, ab = _verified_assertions(a), _verified_assertions(b)
    if not ea or not eb or not aa or not ab:
        return None

    for x in aa:
        for y in ab:
            codes = frozenset({x.capability_type.code, y.capability_type.code})
            pattern = COMPLEMENT_PATTERNS.get(codes)
            if not pattern:
                continue
            evidence_ids = sorted({str(e.id) for e in ea + eb})
            assertion_evidence_ids = sorted({
                str(e.id) for assertion in (x, y)
                for e in assertion.evidences if e.validation_status == "VERIFIED"
            })
            all_evidence = sorted(set(evidence_ids + assertion_evidence_ids))
            confidence_floor = min(
                _product_confidence(a), _product_confidence(b),
                float(x.confidence_score or 0), float(y.confidence_score or 0),
            )
            return {
                "capability_codes": [x.capability_type.code, y.capability_type.code],
                "capability_assertion_ids": [str(x.id), str(y.id)],
                "verified_evidence_ids": all_evidence,
                "confidence_floor": round(confidence_floor, 6),
                "pattern": pattern,
            }
    return None


def _text_matches(product, needle):
    return needle in " ".join([
        product.name or "", product.category or "", product.description or "", product.goal or "",
        *(r.goal or "" for r in product.investment_requests if r.status == "VERIFIED"),
    ]).casefold()


def _has_support_type(product, support_type):
    return support_type in [getattr(x, "value", x) for x in (product.support_types or [])]


def _result(a, b, candidate):
    needs = _need_signals(a) + _need_signals(b)
    return {
        "engine": "investment_opportunity_explorer_v1",
        "status": "POTENTIAL",
        "opportunity_type": "INVESTMENT_COLLABORATION_EXPLORATION",
        "title": f"Potential opportunity: {a.name} × {b.name}",
        "description": candidate["pattern"],
        "confidence_floor": candidate["confidence_floor"],
        "products": [
            {
                "id": str(p.id), "name": p.name,
                "activity_domain": getattr(p.activity_domain, "value", p.activity_domain),
                "category": p.category,
                "goal": p.goal,
                "support_types": [getattr(x, "value", x) for x in (p.support_types or [])],
                "capacity": _capacity(p),
                "need_signals": _need_signals(p),
                "verified_evidence_ids": [str(e.id) for e in _verified_evidence(p)],
            }
            for p in (a, b)
        ],
        "capability_pattern": {
            "codes": candidate["capability_codes"],
            "assertion_ids": candidate["capability_assertion_ids"],
        },
        "evidence_trace": {
            "verified_evidence_ids": candidate["verified_evidence_ids"],
            "intent_signal_types": sorted({n.get("type") for n in needs}),
            "source_rule": "VERIFIED_PRODUCT + VERIFIED_CAPABILITY + VERIFIED_EVIDENCE",
        },
        "explanation": [
            "Both products are VERIFIED.",
            "Both products have at least one VERIFIED evidence item.",
            "The matched capabilities are VERIFIED and have a known complementarity pattern.",
            "Product goals, verified support requests, and production capacity are shown as context; they are not treated as proof of feasibility or investment suitability.",
        ],
        "limitations": [
            "Potential opportunity only; not investment advice or a feasibility assessment.",
            "No ranking of communities or products is performed.",
            "Semantic matching and financial due diligence are not part of this v1 engine.",
        ],
    }


async def _find_existing_opportunity(db, product_ids):
    rows = await db.execute(
        select(Opportunity)
        .join(OpportunityProduct, OpportunityProduct.opportunity_id == Opportunity.id)
        .where(OpportunityProduct.product_id.in_(product_ids))
        .group_by(Opportunity.id)
        .having(func.count(OpportunityProduct.product_id) == len(product_ids))
    )
    for opportunity in rows.scalars().all():
        linked = await db.execute(
            select(OpportunityProduct.product_id).where(OpportunityProduct.opportunity_id == opportunity.id)
        )
        if {str(x) for x in linked.scalars().all()} == {str(x) for x in product_ids}:
            return opportunity
    return None


async def _persist_result(db, a, b, candidate, result):
    product_ids = [a.id, b.id]
    existing = await _find_existing_opportunity(db, product_ids)
    if existing:
        result["opportunity_id"] = str(existing.id)
        return existing

    opportunity = Opportunity(
        title=result["title"],
        opportunity_type=result["opportunity_type"],
        status="POTENTIAL",
        description=result["description"],
        rationale={
            "source": "INVESTMENT_OPPORTUNITY_EXPLORER",
            "product_ids": [str(x) for x in product_ids],
            "capability_assertion_ids": candidate["capability_assertion_ids"],
            "verified_evidence_ids": candidate["verified_evidence_ids"],
            "capability_codes": candidate["capability_codes"],
            "confidence_floor": candidate["confidence_floor"],
            "method": "investment_explorer_over_verified_products",
            "review_gate": "POTENTIAL -> HUMAN_REVIEW -> APPROVED_FOR_INVESTOR_ACCESS",
            "note": "Potential opportunity only; no investment suitability or feasibility conclusion.",
        },
    )
    db.add(opportunity)
    await db.flush()
    db.add_all([
        OpportunityProduct(opportunity_id=opportunity.id, product_id=a.id),
        OpportunityProduct(opportunity_id=opportunity.id, product_id=b.id),
        OpportunityAssertion(opportunity_id=opportunity.id, assertion_id=UUID(candidate["capability_assertion_ids"][0])),
        OpportunityAssertion(opportunity_id=opportunity.id, assertion_id=UUID(candidate["capability_assertion_ids"][1])),
        ReasoningRun(
            opportunity_id=opportunity.id,
            engine="investment_opportunity_explorer_v1",
            status="COMPLETED",
            actor="system",
            result=result,
        ),
    ])
    await db.flush()
    result["opportunity_id"] = str(opportunity.id)
    return opportunity


async def explore_investment_opportunities(
    db: AsyncSession,
    *,
    query: str | None = None,
    activity_domain: str | None = None,
    support_type: str | None = None,
    limit: int = 20,
):
    stmt = (
        select(Product)
        .join(UserProfile, UserProfile.id == Product.profile_id)
        .options(
            selectinload(Product.evidences),
            selectinload(Product.production_capacity),
            selectinload(Product.investment_requests),
            selectinload(Product.capability_assertions).selectinload(CapabilityAssertion.capability_type),
            selectinload(Product.capability_assertions).selectinload(CapabilityAssertion.evidences),
        )
        .where(Product.verification_status == "VERIFIED")
        .order_by(Product.created_at)
    )
    if activity_domain:
        stmt = stmt.where(Product.activity_domain == activity_domain)

    products = (await db.scalars(stmt)).all()
    products = [
        p for p in products
        if getattr(p.verification_status, "value", p.verification_status) == "VERIFIED"
        and _verified_evidence(p)
        and _verified_assertions(p)
    ]

    if activity_domain:
        products = [p for p in products if getattr(p.activity_domain, "value", p.activity_domain) == activity_domain]
    if support_type:
        products = [p for p in products if _has_support_type(p, support_type)]
    if query:
        needle = query.casefold().strip()
        products = [p for p in products if _text_matches(p, needle)]

    if not products:
        return []

    results = []
    seen = set()
    for a, b in combinations(products, 2):
        candidate = _candidate(a, b)
        if not candidate:
            continue
        key = tuple(sorted([str(a.id), str(b.id)])) + tuple(sorted(candidate["capability_codes"]))
        if key in seen:
            continue
        seen.add(key)

        result = _result(a, b, candidate)
        await _persist_result(db, a, b, candidate, result)
        results.append(result)
        if len(results) >= limit:
            break

    await db.commit()
    return results
