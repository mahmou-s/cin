from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...models import Community, CapabilityType, CapabilityAssertion, Evidence, AssertionEvidence, Opportunity, OpportunityAssertion, Scenario, ScenarioStep

router = APIRouter()

@router.get('/search')
async def unified_search(q: str = Query(min_length=2, max_length=200), limit: int = Query(20, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    term = f'%{q.strip()}%'
    communities = (await db.scalars(select(Community).where(or_(Community.name.ilike(term), Community.location.ilike(term), Community.description.ilike(term))).limit(limit))).all()
    capabilities = (await db.scalars(select(CapabilityType).where(or_(CapabilityType.code.ilike(term), CapabilityType.name.ilike(term), CapabilityType.domain.ilike(term), CapabilityType.description.ilike(term))).limit(limit))).all()
    opportunities = (await db.scalars(select(Opportunity).where(or_(Opportunity.title.ilike(term), Opportunity.description.ilike(term))).limit(limit))).all()
    scenarios = (await db.scalars(select(Scenario).where(Scenario.goal.ilike(term)).limit(limit))).all()
    return {'query': q, 'items': [
        *[{'type':'community','id':str(x.id),'title':x.name,'subtitle':x.location or x.country_code} for x in communities],
        *[{'type':'capability','id':str(x.id),'title':f'{x.code} · {x.name}','subtitle':x.domain} for x in capabilities],
        *[{'type':'opportunity','id':str(x.id),'title':x.title,'subtitle':x.opportunity_type} for x in opportunities],
        *[{'type':'scenario','id':str(x.id),'title':x.goal,'subtitle':x.status} for x in scenarios],
    ]}

@router.get('/communities/{community_id}/intelligence-profile')
async def intelligence_profile(community_id: UUID, db: AsyncSession = Depends(get_db)):
    community = await db.get(Community, community_id)
    if not community:
        raise HTTPException(404, 'COMMUNITY_NOT_FOUND')
    rows = (await db.execute(
        select(CapabilityAssertion, CapabilityType)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .where(CapabilityAssertion.community_id == community_id, CapabilityAssertion.status == 'VERIFIED')
        .order_by(CapabilityType.code)
    )).all()
    capabilities = []
    for assertion, capability in rows:
        evidence_count = await db.scalar(select(func.count()).select_from(AssertionEvidence).where(AssertionEvidence.assertion_id == assertion.id))
        capabilities.append({
            'assertion_id': str(assertion.id), 'code': capability.code, 'name': capability.name,
            'domain': capability.domain, 'scope': assertion.scope, 'scale': assertion.scale,
            'quantity': assertion.quantity, 'unit': assertion.unit, 'maturity_level': assertion.maturity_level,
            'confidence_score': assertion.confidence_score, 'confidence_level': assertion.confidence_level,
            'evidence_count': evidence_count or 0,
        })
    opportunity_rows = (await db.execute(
        select(Opportunity).join(OpportunityAssertion, OpportunityAssertion.opportunity_id == Opportunity.id)
        .join(CapabilityAssertion, CapabilityAssertion.id == OpportunityAssertion.assertion_id)
        .where(CapabilityAssertion.community_id == community_id).distinct().order_by(Opportunity.created_at.desc()).limit(30)
    )).scalars().all()
    scenario_rows = (await db.execute(
        select(Scenario).join(ScenarioStep, ScenarioStep.scenario_id == Scenario.id)
        .join(CapabilityAssertion, CapabilityAssertion.id == ScenarioStep.assertion_id)
        .where(CapabilityAssertion.community_id == community_id).distinct().order_by(Scenario.created_at.desc()).limit(30)
    )).scalars().all()
    evidence_total = sum(x['evidence_count'] for x in capabilities)
    return {
        'community': {'id': str(community.id), 'name': community.name, 'country_code': community.country_code, 'location': community.location, 'population': community.population, 'description': community.description},
        'verified_capabilities': capabilities,
        'evidence_count': evidence_total,
        'opportunities': [{'id':str(x.id),'title':x.title,'type':x.opportunity_type,'status':x.status,'description':x.description} for x in opportunity_rows],
        'scenarios': [{'id':str(x.id),'goal':x.goal,'status':x.status,'created_at':x.created_at.isoformat()} for x in scenario_rows],
        'principles': ['الملف يصف القدرات الموثقة ولا يصنف المجتمع.','الثقة في الادعاء لا تساوي قوة القدرة.','وجود علاقة أو فرصة لا يثبت نجاح مشروع أو جدواه الاقتصادية.']
    }
