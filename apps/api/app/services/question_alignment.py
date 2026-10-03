"""Wave 5 question alignment: choose the next question by decision value, not only language overlap."""
import re
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import (
    CINQuestion, CINQuestionAnswer, CINQuestionKnowledgeLink, CINQuestionIntelligenceSignal,
    ClientIntelligenceProfile, CapabilityAssertion, CapabilityType, Evidence, AssertionEvidence,
    Opportunity, InvestmentSupportRequest, UserProfile
)

STOP=set('the and for with from that this your you are our to of in a an on is it or as at by be can do what which how does most now main primary organization right'.split())

def tokens(text):
    return set(w.lower() for w in re.findall(r'[\w\u0600-\u06ff]{4,}', text or '') if w.lower() not in STOP)

def qtokens(q):
    return tokens(f"{q.text} {' '.join(q.options or [])}")

def overlap(a,b):
    if not a or not b: return 0.0
    return min(1.0, len(a & b)/3.0)

async def _context(db, profile):
    caps=(await db.execute(
        select(CapabilityType.name, CapabilityType.domain, CapabilityAssertion.id, CapabilityAssertion.confidence_score, CapabilityAssertion.confidence_level)
        .join(CapabilityAssertion, CapabilityAssertion.capability_type_id==CapabilityType.id)
        .limit(300)
    )).all()
    opps=(await db.scalars(select(Opportunity).order_by(Opportunity.updated_at.desc()).limit(200))).all()
    needs=(await db.execute(
        select(InvestmentSupportRequest.goal, InvestmentSupportRequest.details)
        .join(UserProfile, UserProfile.id==InvestmentSupportRequest.profile_id)
        .limit(200)
    )).all()
    return caps,opps,needs

async def rank_questions(db: AsyncSession, profile, session=None):
    qs=(await db.scalars(select(CINQuestion).where(CINQuestion.segment==profile.segment,CINQuestion.status=='ACTIVE'))).all()
    answered=set()
    if session:
        answered={a.question_id for a in (await db.scalars(select(CINQuestionAnswer).where(CINQuestionAnswer.session_id==session.id))).all()}
    caps,opps,needs=await _context(db,profile)
    cap_text=tokens(' '.join(f'{n} {d}' for n,d,_,_,_ in caps))
    opp_text=tokens(' '.join(f'{o.title} {o.description} {o.rationale}' for o in opps))
    need_text=tokens(' '.join(f'{g or ""} {d or ""}' for g,d in needs))
    risk_text=tokens(' '.join(profile.constraints or [])+' '+' '.join(profile.strategic_objectives or [])) | tokens('risk resilience dependency liquidity continuity succession constraint')
    result=[]
    for q in qs:
        if q.id in answered: continue
        qt=qtokens(q)
        capability=overlap(qt,cap_text)
        opportunity=overlap(qt,opp_text)
        need=overlap(qt,need_text)
        risk=overlap(qt,risk_text)
        matched_assertions=[r for r in caps if tokens(f'{r[0]} {r[1]}') & qt]
        gap=0.0
        refs={'matched_assertions':0,'opportunities':0,'needs':0}
        if matched_assertions:
            refs['matched_assertions']=len(matched_assertions)
            low=sum(1 for r in matched_assertions if (r[3] or 0)<0.70 or str(r[4]).upper() not in ('HIGH','VERIFIED'))
            gap=min(1.0, low/max(1,len(matched_assertions)))
        refs['opportunities']=sum(1 for o in opps if tokens(f'{o.title} {o.description}') & qt)
        refs['needs']=sum(1 for g,d in needs if tokens(f'{g or ""} {d or ""}') & qt)
        base=min(1.0,(0.30*overlap(qt,tokens(' '.join(profile.strategic_objectives or []))) +
                       0.20*overlap(qt,tokens(' '.join(profile.constraints or []))) +
                       0.10*(1.0 if not (qt & tokens(' '.join(profile.strategic_objectives or []))) else 0.35)))
        value=(0.35*base)+(0.15*capability)+(0.20*gap)+(0.15*opportunity)+(0.05*need)+(0.10*risk)
        reasons=[]
        if capability: reasons.append('CAPABILITY_CONTEXT')
        if gap: reasons.append('EVIDENCE_GAP')
        if opportunity: reasons.append('OPPORTUNITY_CONTEXT')
        if need: reasons.append('NEED_CONTEXT')
        if risk: reasons.append('RISK_CONTEXT')
        if not reasons: reasons.append('BASELINE_INFORMATION_GAIN')
        signal=CINQuestionIntelligenceSignal(question_id=q.id,profile_id=profile.id,session_id=session.id if session else None,
            capability_signal=capability,evidence_gap_signal=gap,opportunity_signal=opportunity,need_signal=need,risk_signal=risk,
            intelligence_value=value,reason_codes=reasons,context_refs=refs,created_at=datetime.utcnow())
        db.add(signal)
        result.append((value,q,reasons,signal))
    result.sort(key=lambda x:(-x[0], x[1].priority or 100, x[1].usage_count or 0))
    await db.flush()
    return result
