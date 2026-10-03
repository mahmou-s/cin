"""Evidence-grounded discovery over Products + verified Capabilities.

This layer deliberately does not use UserProfile as the discovery unit. A candidate
is emitted only when both products have verified evidence and each is linked to a
verified capability assertion. The result is a potential opportunity, not a ranking,
recommendation, feasibility proof, or investment advice.
"""
from itertools import combinations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import (
    Product, ProductEvidence, Evidence, ProductCapabilityAssertion,
    CapabilityAssertion, CapabilityType, UserProfile, Opportunity, OpportunityProduct,
    OpportunityAssertion,
)

COMPLEMENT_PATTERNS = {
    frozenset({"C01", "C03"}): "Production capability + export capability may support a market-access collaboration.",
    frozenset({"C01", "C06"}): "Production capability + technology capability may support technology adoption or process improvement.",
    frozenset({"C01", "C02"}): "Production capability + market capability may support a production-to-market collaboration.",
    frozenset({"C04", "C05"}): "Human capital capability + knowledge capability may support training or knowledge transfer.",
    frozenset({"C05", "C07"}): "Knowledge capability + innovation capability may support research-to-innovation collaboration.",
    frozenset({"C06", "C07"}): "Technology capability + innovation capability may support technology development.",
    frozenset({"C08", "C09"}): "Institutional capability + cooperation capability may support coordination.",
    frozenset({"C09", "C10"}): "Cooperation capability + external connectivity may support cross-community connection.",
    frozenset({"C01", "C11"}): "Production capability + logistics capability may support distribution and market access.",
    frozenset({"C03", "C11"}): "Export capability + logistics capability may support international fulfillment and trade movement.",
    frozenset({"C10", "C11"}): "External connectivity + logistics capability may support cross-border movement and access.",
    frozenset({"C02", "C11"}): "Market capability + logistics capability may support supply-to-market coordination.",
}


def _verified_evidence(product):
    return [e for e in product.evidences if e.validation_status == "VERIFIED"]


def _product_confidence(product):
    return float(product.ai_confidence_score or 0.0)


def _candidate(product_a, product_b):
    if product_a.profile_id == product_b.profile_id:
        return None
    evidence_a = _verified_evidence(product_a)
    evidence_b = _verified_evidence(product_b)
    if not evidence_a or not evidence_b:
        return None
    for assertion_a in product_a.capability_assertions:
        for assertion_b in product_b.capability_assertions:
            if assertion_a.status != "VERIFIED" or assertion_b.status != "VERIFIED":
                continue
            code_a = assertion_a.capability_type.code
            code_b = assertion_b.capability_type.code
            pattern = COMPLEMENT_PATTERNS.get(frozenset({code_a, code_b}))
            if not pattern:
                continue
            evidence_ids = [str(e.id) for e in evidence_a + evidence_b]
            capability_evidence = []
            for assertion in (assertion_a, assertion_b):
                capability_evidence.extend(str(e.id) for e in assertion.evidences if e.validation_status == "VERIFIED")
            confidence = min(_product_confidence(product_a), _product_confidence(product_b),
                             float(assertion_a.confidence_score or 0), float(assertion_b.confidence_score or 0))
            return {
                "product_ids": [str(product_a.id), str(product_b.id)],
                "assertion_ids": [str(assertion_a.id), str(assertion_b.id)],
                "evidence_ids": sorted(set(evidence_ids + capability_evidence)),
                "capability_codes": [code_a, code_b],
                "pattern": pattern,
                "confidence_floor": round(confidence, 6),
            }
    return None


async def discover_product_opportunities(db: AsyncSession, limit: int = 50):
    products = (await db.scalars(
        select(Product)
        .join(UserProfile, UserProfile.id == Product.profile_id)
        .where(Product.verification_status == "VERIFIED")
        .options(
            __import__("sqlalchemy").orm.selectinload(Product.evidences),
            __import__("sqlalchemy").orm.selectinload(Product.capability_assertions).selectinload(CapabilityAssertion.capability_type),
            __import__("sqlalchemy").orm.selectinload(Product.capability_assertions).selectinload(CapabilityAssertion.evidences),
        )
        .order_by(Product.created_at)
    )).all()
    products = [p for p in products if _verified_evidence(p) and p.capability_assertions]
    output = []
    seen = set()
    for product_a, product_b in combinations(products, 2):
        candidate = _candidate(product_a, product_b)
        if not candidate:
            continue
        key = tuple(sorted(candidate["product_ids"])) + tuple(sorted(candidate["capability_codes"]))
        if key in seen:
            continue
        seen.add(key)
        existing = await db.scalar(
            select(Opportunity).join(OpportunityProduct, OpportunityProduct.opportunity_id == Opportunity.id)
            .where(OpportunityProduct.product_id.in_([product_a.id, product_b.id]))
            .group_by(Opportunity.id)
            .having(__import__('sqlalchemy').func.count(OpportunityProduct.product_id) == 2)
        )
        if existing:
            output.append(existing)
            if len(output) >= limit:
                break
            continue
        title = f"Potential product collaboration: {product_a.name} × {product_b.name}"
        opportunity = Opportunity(
            title=title,
            opportunity_type="PRODUCT_CAPABILITY_DISCOVERY",
            status="PROPOSED",
            description=candidate["pattern"],
            rationale={
                "source": "PRODUCT_CAPABILITY_EVIDENCE",
                "product_ids": candidate["product_ids"],
                "capability_assertion_ids": candidate["assertion_ids"],
                "verified_evidence_ids": candidate["evidence_ids"],
                "capability_codes": candidate["capability_codes"],
                "confidence_floor": candidate["confidence_floor"],
                "method": "complementary_capabilities_over_verified_products",
                "note": "Potential opportunity only; not a ranking, recommendation, feasibility proof, or investment advice.",
            },
        )
        db.add(opportunity)
        await db.flush()
        db.add_all([
            OpportunityProduct(opportunity_id=opportunity.id, product_id=product_a.id),
            OpportunityProduct(opportunity_id=opportunity.id, product_id=product_b.id),
        ])
        db.add_all([
            OpportunityAssertion(opportunity_id=opportunity.id, assertion_id=__import__("uuid").UUID(candidate["assertion_ids"][0])),
            OpportunityAssertion(opportunity_id=opportunity.id, assertion_id=__import__("uuid").UUID(candidate["assertion_ids"][1])),
        ])
        output.append(opportunity)
        if len(output) >= limit:
            break
    await db.commit()
    return output
