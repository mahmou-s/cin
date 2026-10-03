from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...db import get_db
from ...models import Opportunity, OpportunityAssertion, CapabilityAssertion, CapabilityType, Community
from ...services.opportunities import discover_opportunities
from ...auth import Principal, require_authenticated

router = APIRouter()

@router.post("/opportunities/discover")
async def discover(limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    items = await discover_opportunities(db, limit)
    return {"count": len(items), "items": [await _serialize(db, x) for x in items]}

@router.get("/opportunities")
async def opportunities(status: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Opportunity).order_by(Opportunity.created_at.desc())
    if status:
        q = q.where(Opportunity.status == status)
    items = (await db.scalars(q)).all()
    return {"count": len(items), "items": [await _serialize(db, x) for x in items]}

async def _serialize(db, item):
    rows = await db.execute(
        select(CapabilityAssertion.id, CapabilityType.code, CapabilityType.name, Community.id, Community.name)
        .join(OpportunityAssertion, OpportunityAssertion.assertion_id == CapabilityAssertion.id)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(OpportunityAssertion.opportunity_id == item.id)
    )
    return {
        "id": str(item.id), "title": item.title, "type": item.opportunity_type,
        "status": item.status, "description": item.description,
        "rationale": item.rationale,
        "capabilities": [{"assertion_id": str(a), "code": code, "name": name, "community_id": str(cid), "community_name": cname} for a, code, name, cid, cname in rows.all()]
    }

@router.post("/opportunities/discover/products")
async def discover_products(limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    """Evidence-grounded discovery over verified Products and verified CapabilityAssertions."""
    from ...services.product_opportunity_discovery import discover_product_opportunities
    items = await discover_product_opportunities(db, limit)
    return {"count": len(items), "items": [await _serialize_product_opportunity(db, x) for x in items]}


async def _serialize_product_opportunity(db, item):
    from ...models import OpportunityProduct, Product, ProductCapabilityAssertion, Evidence
    product_rows = await db.execute(
        select(Product.id, Product.name, Product.profile_id)
        .join(OpportunityProduct, OpportunityProduct.product_id == Product.id)
        .where(OpportunityProduct.opportunity_id == item.id)
    )
    assertion_rows = await db.execute(
        select(CapabilityAssertion.id, CapabilityType.code, CapabilityType.name)
        .join(OpportunityAssertion, OpportunityAssertion.assertion_id == CapabilityAssertion.id)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .where(OpportunityAssertion.opportunity_id == item.id)
    )
    return {
        "id": str(item.id),
        "title": item.title,
        "type": item.opportunity_type,
        "status": item.status,
        "description": item.description,
        "rationale": item.rationale,
        "products": [{"id": str(pid), "name": name, "profile_id": str(profile_id)} for pid, name, profile_id in product_rows.all()],
        "capabilities": [{"assertion_id": str(aid), "code": code, "name": name} for aid, code, name in assertion_rows.all()],
        "verified_evidence_ids": item.rationale.get("verified_evidence_ids", []),
    }


@router.get("/opportunities/explorer")
async def investment_explorer(
    query: str | None = Query(None, min_length=1, max_length=200),
    activity_domain: str | None = Query(None, max_length=40),
    support_type: str | None = Query(None, max_length=40),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_authenticated),
):
    """Explainable investment-opportunity exploration over verified Products, Capabilities and Evidence."""
    from ...services.investment_opportunity_explorer import explore_investment_opportunities
    items = await explore_investment_opportunities(
        db, query=query, activity_domain=activity_domain, support_type=support_type, limit=limit
    )
    return {"count": len(items), "items": items}
