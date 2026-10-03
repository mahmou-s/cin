from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import CapabilityAssertion, CapabilityType, Community, Opportunity, OpportunityAssertion

# These are domain-level complementarity patterns, not rankings.
COMPLEMENT_PATTERNS = {
    frozenset({"C01", "C03"}): "Production capability + export capability can support a potential market-access collaboration.",
    frozenset({"C01", "C06"}): "Production capability + technology capability can support a potential technology adoption or process-improvement collaboration.",
    frozenset({"C01", "C02"}): "Production capability + market capability can support a potential production-to-market collaboration.",
    frozenset({"C04", "C05"}): "Human capital capability + knowledge capability can support a potential training or knowledge-transfer collaboration.",
    frozenset({"C05", "C07"}): "Knowledge capability + innovation capability can support a potential research-to-innovation collaboration.",
    frozenset({"C06", "C07"}): "Technology capability + innovation capability can support a potential technology-development collaboration.",
    frozenset({"C08", "C09"}): "Institutional capability + cooperation capability can support a potential coordination collaboration.",
    frozenset({"C09", "C10"}): "Cooperation capability + external connectivity capability can support a potential cross-community connection.",
}

async def discover_opportunities(db: AsyncSession, limit: int = 50):
    rows = await db.execute(
        select(CapabilityAssertion, CapabilityType, Community)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(CapabilityAssertion.status == "VERIFIED")
    )
    records = rows.all()
    candidates = []
    for i, (a1, t1, c1) in enumerate(records):
        for a2, t2, c2 in records[i + 1:]:
            if a1.community_id == a2.community_id or t1.code == t2.code:
                continue
            pattern = COMPLEMENT_PATTERNS.get(frozenset({t1.code, t2.code}))
            if not pattern:
                continue
            candidates.append((a1, t1, c1, a2, t2, c2, pattern))
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break

    output = []
    for a1, t1, c1, a2, t2, c2, pattern in candidates:
        existing = await db.scalar(
            select(Opportunity).join(OpportunityAssertion, OpportunityAssertion.opportunity_id == Opportunity.id)
            .where(OpportunityAssertion.assertion_id.in_([a1.id, a2.id]))
            .group_by(Opportunity.id).having(__import__('sqlalchemy').func.count(OpportunityAssertion.assertion_id) == 2)
        )
        if existing:
            output.append(existing)
            continue
        title = f"Potential collaboration: {c1.name} × {c2.name}"
        opportunity = Opportunity(
            title=title,
            description=pattern,
            rationale={
                "principle": "COMPLEMENTARY_CAPABILITIES",
                "capability_codes": [t1.code, t2.code],
                "community_ids": [str(c1.id), str(c2.id)],
                "confidence_levels": [a1.confidence_level, a2.confidence_level],
                "note": "This is a potential opportunity, not a ranking, recommendation, or proof of feasibility."
            }
        )
        db.add(opportunity)
        await db.flush()
        db.add_all([
            OpportunityAssertion(opportunity_id=opportunity.id, assertion_id=a1.id),
            OpportunityAssertion(opportunity_id=opportunity.id, assertion_id=a2.id),
        ])
        output.append(opportunity)
    await db.commit()
    return output
