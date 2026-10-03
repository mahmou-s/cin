from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import CapabilityAssertion, CapabilityType, Community, AssertionEvidence
from .chain_definitions import CHAINS, CHAIN_DEFINITIONS, aggregate_support


async def discover(db: AsyncSession, limit: int = 30):
    rows = (await db.execute(
        select(CapabilityAssertion, CapabilityType, Community)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(CapabilityAssertion.status == 'VERIFIED')
    )).all()
    by_code = {}
    for a, t, c in rows:
        by_code.setdefault(t.code, []).append((a,t,c))

    evidence_counts = {}
    if rows:
        ids = [a.id for a,_,_ in rows]
        evrows = (await db.execute(select(AssertionEvidence.assertion_id).where(AssertionEvidence.assertion_id.in_(ids)))).all()
        for (aid,) in evrows:
            evidence_counts[aid] = evidence_counts.get(aid,0)+1

    results=[]
    for chain, meta in CHAIN_DEFINITIONS.items():
        pools=[by_code.get(code,[]) for code in chain]
        if any(not p for p in pools):
            continue
        combos=[()]
        for pool in pools:
            combos=[x+(item,) for x in combos for item in pool[:8]][:100]
        for combo in combos:
            communities=[]; seen=set(); steps=[]; scores=[]
            for a,t,c in combo:
                if c.id not in seen:
                    communities.append({'id':str(c.id),'name':c.name}); seen.add(c.id)
                score=float(a.confidence_score or 0)
                scores.append(score)
                steps.append({
                    'code':t.code,'capability':t.name,'community':c.name,
                    'community_id':str(c.id),'assertion_id':str(a.id),
                    'confidence':score,
                    'evidence_count':evidence_counts.get(a.id,0)
                })
            support = aggregate_support(scores)
            results.append({
                'title':'مسار فرصة حضارية: ' + ' → '.join(chain),
                'capability_chain':list(chain),
                'communities':communities,
                'steps':steps,
                'support':support['weakest_link'],
                'support_weakest_link':support['weakest_link'],
                'support_average':support['average'],
                'rationale':meta['rationale'],
                'status':'POTENTIAL',
                'limitations':[
                    'المسار مبني على قدرات موثقة فقط.',
                    'لا يثبت رغبة أي مجتمع في التعاون.',
                    'لا يثبت الجدوى الاقتصادية أو نجاح المشروع.',
                    'الثقة تقيس دعم الأدلة للادعاء وليست مقياسًا لقوة المجتمع.',
                ]
            })
            if len(results)>=limit:
                return results
    return results
