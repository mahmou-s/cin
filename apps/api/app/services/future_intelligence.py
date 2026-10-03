"""Wave 6: future-oriented question ranking with scenario and readiness awareness.

The service is deterministic and evidence-aware: it prioritizes questions that can
reduce uncertainty about a stated future, scenario exposure, readiness gaps, and
future opportunities. It does not predict outcomes.
"""
import re
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import (CINQuestion, CINQuestionAnswer, CINFutureIntelligenceSignal,
                      ClientIntelligenceProfile, Opportunity, CapabilityAssertion, CapabilityType)

STOP=set('the and for with from that this your you are our to of in a an on is it or as at by be can do what which how does most now next will would should'.split())

def tokens(text):
    return set(w.lower() for w in re.findall(r'[\w\u0600-\u06ff]{4,}', text or '') if w.lower() not in STOP)

def overlap(a,b):
    if not a or not b: return 0.0
    return min(1.0,len(a & b)/3.0)

FUTURE_TERMS='future long-term horizon next years growth expansion transformation continuity succession resilience readiness scenario investment innovation market opportunity children generation'.split()
SCENARIO_TERMS='growth stress opportunity transformation disruption resilience downside upside uncertainty scenario'.split()
READINESS_TERMS='ready readiness capability gap barrier constraint capacity skill capital technology people infrastructure governance'.split()

async def rank_future_questions(db: AsyncSession, profile, session=None):
    qs=(await db.scalars(select(CINQuestion).where(CINQuestion.segment==profile.segment,CINQuestion.status=='ACTIVE'))).all()
    answered=set()
    if session:
        answered={a.question_id for a in (await db.scalars(select(CINQuestionAnswer).where(CINQuestionAnswer.session_id==session.id))).all()}
    future_ctx=tokens(' '.join([profile.desired_future or '', profile.future_horizon or '', ' '.join(profile.preferred_scenarios or []), ' '.join(profile.readiness_barriers or []), ' '.join(profile.strategic_objectives or [])]))
    scenario_ctx=tokens(' '.join(profile.preferred_scenarios or [])) | tokens(' '.join(SCENARIO_TERMS))
    readiness_ctx=tokens(' '.join(profile.readiness_barriers or [])) | tokens(' '.join(READINESS_TERMS))
    opps=(await db.scalars(select(Opportunity).order_by(Opportunity.updated_at.desc()).limit(200))).all()
    opp_ctx=tokens(' '.join(f'{o.title} {o.description}' for o in opps))
    caps=(await db.execute(select(CapabilityType.name,CapabilityType.domain,CapabilityAssertion.confidence_score).join(CapabilityAssertion,CapabilityAssertion.capability_type_id==CapabilityType.id).limit(300))).all()
    cap_ctx=tokens(' '.join(f'{n} {d}' for n,d,_ in caps))
    ranked=[]
    for q in qs:
        if q.id in answered: continue
        qt=tokens(f'{q.text} {" ".join(q.options or [])}')
        future=overlap(qt,future_ctx | tokens(' '.join(FUTURE_TERMS)))
        scenario=overlap(qt,scenario_ctx)
        readiness=overlap(qt,readiness_ctx)
        opp=overlap(qt,opp_ctx)
        capability=overlap(qt,cap_ctx)
        uncertainty=1.0 if not (qt & future_ctx) else 0.45
        score=(0.30*future)+(0.20*scenario)+(0.20*readiness)+(0.15*opp)+(0.05*capability)+(0.10*uncertainty)
        reasons=[]
        if future: reasons.append('FUTURE_ALIGNMENT')
        if scenario: reasons.append('SCENARIO_RELEVANCE')
        if readiness: reasons.append('READINESS_GAP')
        if opp: reasons.append('FUTURE_OPPORTUNITY')
        if uncertainty >= 0.8: reasons.append('UNCERTAINTY_REDUCTION')
        if not reasons: reasons.append('FUTURE_BASELINE')
        refs={'opportunities':sum(1 for o in opps if tokens(f'{o.title} {o.description}') & qt),'capabilities':sum(1 for n,d,_ in caps if tokens(f'{n} {d}') & qt)}
        sig={'future_alignment':future,'scenario_relevance':scenario,'readiness_gap':readiness,'opportunity_future_signal':opp,'uncertainty_signal':uncertainty,'future_intelligence_value':score,'reason_codes':reasons,'context_refs':refs}
        db.add(CINFutureIntelligenceSignal(question_id=q.id,profile_id=profile.id,session_id=session.id if session else None,created_at=datetime.utcnow(),**sig))
        ranked.append((score,q,reasons,sig))
    ranked.sort(key=lambda x:(-x[0],x[1].priority or 100,x[1].usage_count or 0))
    await db.flush()
    return ranked
