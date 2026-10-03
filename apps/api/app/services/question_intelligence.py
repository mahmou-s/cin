import re
from datetime import datetime
from sqlalchemy import select, func
from ..models import ClientIntelligenceProfile, CINQuestion, CINQuestionSession, CINQuestionAnswer, CINQuestionPattern, CINQuestionKnowledgeLink, CINQuestionPrioritySignal

STOP=set('the and for with from that this your you are our to of in a an on is it or as at by be can do what which how does most now'.split())
def concepts(text):
    words=[w.lower() for w in re.findall(r'[\w\u0600-\u06ff]{4,}', text or '') if w.lower() not in STOP]
    return list(dict.fromkeys(words[:12]))

DEFAULTS={
 'OTHER':[('future_vision','What future would you most like this organization to achieve?',['Sustainable growth','Greater resilience','New markets','Transformation','Continuity','Social impact','Other']),('scenario_choice','Which future situation would you most like CIN to help you prepare for?',['Growth','Stress or disruption','Major opportunity','Leadership transition','Market change','Technology change','Other']),('readiness_gap','What is the biggest gap between where you are now and where you want to be?',['Capital','People and skills','Technology','Market access','Infrastructure','Partnerships','Other']),('strategic_priority','What is the main strategic priority for your organization right now?',['Growth','Risk reduction','Liquidity','Expansion','Efficiency','Continuity','New opportunities']),
          ('decision_gap','Which decision would benefit most from better intelligence?',['Growth investment','Risk management','Capital allocation','Operations','Partnerships','Market entry'])],
 'FAMILY_OFFICE':[('strategic_priority','What is the family office primarily trying to achieve?',['Preserve wealth','Grow wealth','Succession','Diversification','Liquidity','Impact']),('decision_gap','Where is better intelligence most valuable?',['Portfolio risk','Private markets','Succession','Liquidity','Opportunities','Governance'])],
 'ASSET_MANAGER':[('strategic_priority','What is the primary institutional objective?',['Asset growth','Risk management','Client solutions','Operational efficiency','New strategies','Data and AI']),('decision_gap','Where is the biggest intelligence gap?',['Portfolio risk','Client needs','Market research','Private markets','Operations','Technology'])],
 'PENSION_FUND':[('strategic_priority','What is the main priority?',['Long-term return','Liability management','Risk','Liquidity','Governance','Funding resilience'])],
 'INSURER':[('strategic_priority','What is the main priority?',['Capital efficiency','Risk','Liquidity','Investment return','Liability matching','Growth'])],
 'BANK':[('strategic_priority','What is the main priority?',['Capital','Risk','Liquidity','Customer growth','Operations','Technology'])],
 'CORPORATION':[('strategic_priority','What is the main priority?',['Growth','Efficiency','Market expansion','Capital','Supply chain','Innovation'])],
 'GOVERNMENT':[('strategic_priority','What is the main development priority?',['Economic growth','Infrastructure','Employment','Investment','Public services','Resilience'])],
 'FAMILY_BUSINESS':[('strategic_priority','What is the most important priority for the business and family?',['Growth','Continuity','Succession','Capital','New markets','Professionalization'])]
}

def seed_question_rows(segment):
    base=DEFAULTS.get(segment, DEFAULTS['OTHER'])
    future=[
        ('future_vision','What future outcome would you most like to achieve over your planning horizon?',['Sustainable growth','Greater resilience','New markets','Transformation','Continuity','Social impact','Other']),
        ('future_scenario','Which scenario would you most like CIN to help you prepare for?',['Growth','Stress or disruption','Major opportunity','Leadership transition','Market change','Technology change','Other']),
        ('readiness_gap','What is the biggest gap between your current position and the future you want?',['Capital','People and skills','Technology','Market access','Infrastructure','Partnerships','Other']),
    ]
    keys={x[0] for x in base}
    return base + [x for x in future if x[0] not in keys]

async def ensure_questions(db, segment):
    for key,text,opts in seed_question_rows(segment):
        q=await db.scalar(select(CINQuestion).where(CINQuestion.question_key==f'{segment}:{key}'))
        if not q:
            q=CINQuestion(question_key=f'{segment}:{key}',segment=segment,text=text,options=opts,status='ACTIVE',priority=100,created_at=datetime.utcnow(),updated_at=datetime.utcnow())
            db.add(q)
    await db.flush()
    return (await db.scalars(select(CINQuestion).where(CINQuestion.segment==segment,CINQuestion.status=='ACTIVE').order_by(CINQuestion.priority,CINQuestion.created_at))).all()


def _token_set(text):
    return set(concepts(text or ''))

def _question_concepts(q):
    return _token_set(f"{q.text} {' '.join(q.options or [])}")

async def index_question_knowledge(db, q):
    """Build a lightweight knowledge-graph projection from question language.
    This is deliberately deterministic and auditable; semantic embeddings can be added later.
    """
    existing=(await db.scalars(select(CINQuestionKnowledgeLink).where(CINQuestionKnowledgeLink.question_id==q.id))).all()
    existing_keys={x.concept_key for x in existing}
    for key in _question_concepts(q):
        if key not in existing_keys:
            db.add(CINQuestionKnowledgeLink(question_id=q.id, concept_key=key, concept_type='QUESTION_CONCEPT', relevance_score=1.0, evidence_state='UNKNOWN', created_at=datetime.utcnow(), updated_at=datetime.utcnow()))

async def prioritize_questions(db, profile, session=None):
    qs=(await db.scalars(select(CINQuestion).where(CINQuestion.segment==profile.segment,CINQuestion.status=='ACTIVE'))).all()
    answers=[]
    if session:
        answers=(await db.scalars(select(CINQuestionAnswer).where(CINQuestionAnswer.session_id==session.id))).all()
    answered_ids={a.question_id for a in answers}
    context=' '.join(profile.strategic_objectives or [])+' '+' '.join(profile.constraints or [])+' '+(profile.decision_horizon or '')+' '+(profile.readiness_level or '')+' '+' '.join([c for a in answers for c in (a.extracted_concepts or [])])
    ctx=_token_set(context)
    scored=[]
    for q in qs:
        if q.id in answered_ids: continue
        await index_question_knowledge(db,q)
        qtokens=_question_concepts(q)
        objective=_token_set(' '.join(profile.strategic_objectives or [])) & qtokens
        constraints=_token_set(' '.join(profile.constraints or [])) & qtokens
        objective_score=min(1.0,len(objective)/3)
        constraint_score=min(1.0,len(constraints)/2)
        pattern_rows=(await db.scalars(select(CINQuestionPattern).where(CINQuestionPattern.segment==profile.segment))).all()
        pattern_signal=min(1.0, sum(p.occurrence_count for p in pattern_rows if p.concept_key in qtokens)/6)
        validated=sum(1 for p in pattern_rows if p.validated and p.concept_key in qtokens)
        evidence_signal=min(1.0, validated/2)
        novelty=1.0 if not (ctx & qtokens) else 0.35
        total=(objective_score*0.30)+(constraint_score*0.20)+(pattern_signal*0.20)+(evidence_signal*0.20)+(novelty*0.10)+(max(0,100-(q.priority or 100))/1000)
        reasons=[]
        if objective: reasons.append('OBJECTIVE_MATCH')
        if constraints: reasons.append('CONSTRAINT_MATCH')
        if pattern_signal: reasons.append('REPEATED_PATTERN')
        if evidence_signal: reasons.append('VALIDATED_PATTERN')
        if novelty >= 0.8: reasons.append('INFORMATION_GAIN')
        scored.append((total,q,reasons,objective_score,constraint_score,pattern_signal,evidence_signal,novelty))
    scored.sort(key=lambda x:(-x[0], x[1].priority or 100, x[1].usage_count or 0))
    for total,q,reasons,om,cm,ps,es,ns in scored:
        db.add(CINQuestionPrioritySignal(question_id=q.id,profile_id=profile.id,objective_match=om,constraint_match=cm,pattern_signal=ps,evidence_signal=es,novelty_signal=ns,total_score=total,reason_codes=reasons,created_at=datetime.utcnow()))
    await db.flush()
    return [x[1] for x in scored]

async def start_session(db, principal_id, segment):
    qs=await ensure_questions(db,segment)
    s=CINQuestionSession(principal_id=principal_id,segment=segment,current_question_id=qs[0].id if qs else None,completed=False,created_at=datetime.utcnow(),updated_at=datetime.utcnow())
    db.add(s); await db.commit(); await db.refresh(s)
    return s, qs[0] if qs else None

async def submit_answer(db, session, question, mode, selected_option, free_text):
    text=free_text if mode in ('FREE_TEXT','OTHER') else selected_option
    cs=concepts(text)
    a=CINQuestionAnswer(session_id=session.id,question_id=question.id,mode=mode,selected_option=selected_option,free_text=free_text,extracted_concepts=cs,created_at=datetime.utcnow())
    db.add(a); question.usage_count=(question.usage_count or 0)+1
    for c in cs:
        p=await db.scalar(select(CINQuestionPattern).where(CINQuestionPattern.concept_key==c,CINQuestionPattern.segment==session.segment))
        if p: p.occurrence_count+=1; p.updated_at=datetime.utcnow()
        else: db.add(CINQuestionPattern(concept_key=c,normalized_text=text,segment=session.segment,occurrence_count=1,validated=False,created_at=datetime.utcnow(),updated_at=datetime.utcnow()))
    await db.flush()
    # Repeated patterns become governed candidates; never auto-activate.
    for c in cs:
        p=await db.scalar(select(CINQuestionPattern).where(CINQuestionPattern.concept_key==c,CINQuestionPattern.segment==session.segment))
        if p:
            await maybe_generate_candidate(db, p)
    await db.flush()
    profile=await db.scalar(select(ClientIntelligenceProfile).where(ClientIntelligenceProfile.principal_id==session.principal_id))
    if profile:
        from .question_alignment import rank_questions
        enhanced=await rank_questions(db,profile,session)
        nxt=enhanced[0][1] if enhanced else None
    else:
        nxt=await db.scalar(select(CINQuestion).where(CINQuestion.segment==session.segment,CINQuestion.status=='ACTIVE',CINQuestion.id!=question.id).order_by(CINQuestion.usage_count, CINQuestion.priority, CINQuestion.created_at))
    session.current_question_id=nxt.id if nxt else None
    session.completed=nxt is None; session.updated_at=datetime.utcnow()
    await db.commit()
    return a,nxt

QUESTION_LEARNING_MIN_OCCURRENCES = 3
QUESTION_LEARNING_MIN_SESSIONS = 2


def candidate_question_text(concept: str, segment: str):
    label = concept.replace('_', ' ').strip()
    return (
        f"How important is {label} to your organization right now?",
        ["Critical priority", "High priority", "Moderate priority", "Exploratory", "Other"],
    )

async def maybe_generate_candidate(db, pattern):
    """Create a governed CANDIDATE question only after repeated evidence.

    A pattern never becomes an active production question automatically.
    """
    if pattern.validated or pattern.candidate_question_id:
        return None
    if pattern.occurrence_count < QUESTION_LEARNING_MIN_OCCURRENCES:
        return None
    from ..models import CINQuestionAnswer, CINQuestion
    distinct_sessions = int((await db.execute(
        select(func.count(func.distinct(CINQuestionAnswer.session_id)))
        .join(CINQuestion, CINQuestion.id == CINQuestionAnswer.question_id)
        .where(CINQuestion.segment == pattern.segment, CINQuestionAnswer.extracted_concepts.contains([pattern.concept_key]))
    )).scalar() or 0)
    pattern.distinct_session_count = max(1, distinct_sessions)
    if distinct_sessions < QUESTION_LEARNING_MIN_SESSIONS:
        return None
    text, options = candidate_question_text(pattern.concept_key, pattern.segment.value)
    q = CINQuestion(
        question_key=f"{pattern.segment.value}:LEARNED:{pattern.concept_key}",
        segment=pattern.segment,
        text=text,
        options=options,
        allow_free_text=True,
        status='CANDIDATE',
        priority=120,
        usage_count=0,
        created_from_pattern=str(pattern.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(q)
    await db.flush()
    pattern.candidate_question_id = q.id
    pattern.candidate_generated_at = datetime.utcnow()
    return q

async def review_candidate(db, question_id, reviewer_id, decision, note=None):
    from ..models import CINQuestion, CINQuestionPattern
    q = await db.scalar(select(CINQuestion).where(CINQuestion.id == question_id))
    if not q:
        raise ValueError('QUESTION_CANDIDATE_NOT_FOUND')
    if q.status != 'CANDIDATE':
        raise ValueError('QUESTION_CANDIDATE_NOT_REVIEWABLE')
    now = datetime.utcnow()
    q.reviewed_by = reviewer_id
    q.reviewed_at = now
    q.review_note = note
    if decision == 'APPROVE':
        q.status = 'ACTIVE'
        pattern = await db.scalar(select(CINQuestionPattern).where(CINQuestionPattern.candidate_question_id == q.id))
        if pattern:
            pattern.validated = True
            pattern.updated_at = now
    elif decision == 'REJECT':
        q.status = 'RETIRED'
    else:
        raise ValueError('INVALID_QUESTION_REVIEW_DECISION')
    q.updated_at = now
    await db.commit()
    await db.refresh(q)
    return q
