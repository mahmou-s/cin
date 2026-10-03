from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Opportunity, OpportunityAssertion, OpportunityReview, CapabilityAssertion, CapabilityType, Community

DECISIONS = {'ACCEPT','MODIFY','REJECT'}

def _serialize(o):
    return {'id':str(o.id),'title':o.title,'type':o.opportunity_type,'status':o.status,'description':o.description,'rationale':o.rationale,'created_at':o.created_at.isoformat()}

async def queue(db: AsyncSession, limit=50):
    rows=(await db.execute(select(Opportunity).where(Opportunity.status.in_(['PROPOSED','POTENTIAL','UNDER_REVIEW'])).order_by(Opportunity.created_at.desc()).limit(limit))).scalars().all()
    return [_serialize(o) for o in rows]

async def review(db: AsyncSession, opportunity_id, decision, actor, note=None):
    if decision not in DECISIONS: raise ValueError('Invalid decision')
    o=await db.get(Opportunity, opportunity_id)
    if not o: return None
    status={'ACCEPT':'ACCEPTED','MODIFY':'NEEDS_REVISION','REJECT':'REJECTED'}[decision]
    o.status=status
    o.updated_at=__import__('datetime').datetime.utcnow()
    db.add(OpportunityReview(opportunity_id=o.id,decision=decision,actor=actor,note=note))
    await db.commit(); await db.refresh(o)
    return _serialize(o)
