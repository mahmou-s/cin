from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...auth import Principal, require_submitter, require_reviewer
from ...models import ClientIntelligenceProfile, ClientSegment, CINQuestion, CINQuestionSession
from ...schemas import ClientIntelligenceProfileCreate, ClientIntelligenceProfileOut, QuestionSessionStart, CINQuestionOut, QuestionAnswerIn, QuestionAnswerOut
from ...services.question_intelligence import start_session, submit_answer, prioritize_questions
from ...services.question_alignment import rank_questions
from datetime import datetime
router=APIRouter()

def qout(q):
    return CINQuestionOut(id=q.id,question_key=q.question_key,segment=q.segment.value,text=q.text,options=q.options or [],allow_free_text=q.allow_free_text)

@router.get('/client-intelligence/me',response_model=ClientIntelligenceProfileOut)
async def get_profile(db:AsyncSession=Depends(get_db), principal:Principal=Depends(require_submitter)):
    p=await db.scalar(select(ClientIntelligenceProfile).where(ClientIntelligenceProfile.principal_id==principal.subject))
    if not p: raise HTTPException(404,'CLIENT_INTELLIGENCE_PROFILE_NOT_FOUND')
    return p

@router.post('/client-intelligence/me',response_model=ClientIntelligenceProfileOut)
async def upsert_profile(data:ClientIntelligenceProfileCreate,db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_submitter)):
    try: segment=ClientSegment(data.segment)
    except ValueError: raise HTTPException(422,'INVALID_CLIENT_SEGMENT')
    p=await db.scalar(select(ClientIntelligenceProfile).where(ClientIntelligenceProfile.principal_id==principal.subject))
    if not p: p=ClientIntelligenceProfile(principal_id=principal.subject,segment=segment,created_at=datetime.utcnow()); db.add(p)
    p.segment=segment; p.organization_size=data.organization_size; p.strategic_objectives=data.strategic_objectives; p.constraints=data.constraints; p.decision_horizon=data.decision_horizon; p.readiness_level=data.readiness_level; p.desired_future=data.desired_future; p.future_horizon=data.future_horizon; p.preferred_scenarios=data.preferred_scenarios; p.readiness_barriers=data.readiness_barriers; p.profile_confidence=min(1.0,0.2+0.15*len(data.strategic_objectives)+0.1*len(data.constraints)); p.updated_at=datetime.utcnow()
    await db.commit(); await db.refresh(p); return p

@router.post('/questions/sessions',response_model=dict)
async def create_session(data:QuestionSessionStart,db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_submitter)):
    try: segment=ClientSegment(data.segment)
    except ValueError: raise HTTPException(422,'INVALID_CLIENT_SEGMENT')
    s,q=await start_session(db,principal.subject,segment.value)
    return {'session_id':s.id,'question':qout(q) if q else None,'completed':s.completed}

@router.get('/questions/sessions/{session_id}',response_model=dict)
async def get_session(session_id:UUID,db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_submitter)):
    s=await db.scalar(select(CINQuestionSession).where(CINQuestionSession.id==session_id,CINQuestionSession.principal_id==principal.subject))
    if not s: raise HTTPException(404,'QUESTION_SESSION_NOT_FOUND')
    q=await db.scalar(select(CINQuestion).where(CINQuestion.id==s.current_question_id)) if s.current_question_id else None
    return {'session_id':s.id,'question':qout(q) if q else None,'completed':s.completed}

@router.post('/questions/sessions/{session_id}/answer',response_model=QuestionAnswerOut)
async def answer(session_id:UUID,data:QuestionAnswerIn,db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_submitter)):
    s=await db.scalar(select(CINQuestionSession).where(CINQuestionSession.id==session_id,CINQuestionSession.principal_id==principal.subject))
    if not s: raise HTTPException(404,'QUESTION_SESSION_NOT_FOUND')
    if s.completed or not s.current_question_id: raise HTTPException(409,'QUESTION_SESSION_COMPLETED')
    q=await db.scalar(select(CINQuestion).where(CINQuestion.id==s.current_question_id))
    if not q: raise HTTPException(404,'QUESTION_NOT_FOUND')
    if data.mode=='CHOICE' and data.selected_option not in (q.options or []): raise HTTPException(422,'INVALID_OPTION')
    if data.mode in ('FREE_TEXT','OTHER') and not (data.free_text or '').strip(): raise HTTPException(422,'FREE_TEXT_REQUIRED')
    a,nxt=await submit_answer(db,s,q,data.mode,data.selected_option,data.free_text)
    return QuestionAnswerOut(answer_id=a.id,concepts=a.extracted_concepts,next_question=qout(nxt) if nxt else None,completed=s.completed)

@router.get('/questions/patterns',response_model=list[dict])
async def patterns(db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_reviewer)):
    from ...models import CINQuestionPattern
    rows=(await db.scalars(select(CINQuestionPattern).order_by(CINQuestionPattern.occurrence_count.desc()).limit(100))).all()
    return [{'id':p.id,'segment':p.segment.value,'concept_key':p.concept_key,'occurrence_count':p.occurrence_count,'validated':p.validated,'candidate_question_id':p.candidate_question_id} for p in rows]

@router.get('/questions/candidates',response_model=list[dict])
async def question_candidates(db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_reviewer)):
    rows=(await db.scalars(select(CINQuestion).where(CINQuestion.status=='CANDIDATE').order_by(CINQuestion.created_at))).all()
    return [
        {'id':q.id,'segment':q.segment.value,'question_key':q.question_key,'text':q.text,'options':q.options or [],
         'created_from_pattern':q.created_from_pattern,'reviewed_by':q.reviewed_by,'reviewed_at':q.reviewed_at,
         'review_note':q.review_note}
        for q in rows
    ]

@router.post('/questions/candidates/{question_id}/review',response_model=dict)
async def review_question_candidate(question_id:UUID, data:dict, db:AsyncSession=Depends(get_db), principal:Principal=Depends(require_reviewer)):
    decision=str(data.get('decision','')).upper()
    note=data.get('note')
    from ...services.question_intelligence import review_candidate
    try:
        q=await review_candidate(db, question_id, principal.subject, decision, note)
    except ValueError as e:
        raise HTTPException(422,str(e))
    return {'id':q.id,'status':q.status,'reviewed_by':q.reviewed_by,'reviewed_at':q.reviewed_at,'review_note':q.review_note}


@router.get('/questions/sessions/{session_id}/future-ranking',response_model=list[dict])
async def future_question_ranking(session_id:UUID,db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_submitter)):
    s=await db.scalar(select(CINQuestionSession).where(CINQuestionSession.id==session_id,CINQuestionSession.principal_id==principal.subject))
    if not s: raise HTTPException(404,'QUESTION_SESSION_NOT_FOUND')
    p=await db.scalar(select(ClientIntelligenceProfile).where(ClientIntelligenceProfile.principal_id==principal.subject))
    if not p: raise HTTPException(404,'CLIENT_INTELLIGENCE_PROFILE_NOT_FOUND')
    from ...services.future_intelligence import rank_future_questions
    ranked=await rank_future_questions(db,p,s); await db.commit()
    return [{'question_id':q.id,'score':score,'reason_codes':reasons,'question':qout(q),'signals':sig} for score,q,reasons,sig in ranked[:20]]

@router.get('/questions/sessions/{session_id}/ranking',response_model=list[dict])
async def question_ranking(session_id:UUID,db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_submitter)):
    from ...models import CINQuestionPrioritySignal, CINQuestion
    s=await db.scalar(select(CINQuestionSession).where(CINQuestionSession.id==session_id,CINQuestionSession.principal_id==principal.subject))
    if not s: raise HTTPException(404,'QUESTION_SESSION_NOT_FOUND')
    p=await db.scalar(select(ClientIntelligenceProfile).where(ClientIntelligenceProfile.principal_id==principal.subject))
    if not p: raise HTTPException(404,'CLIENT_INTELLIGENCE_PROFILE_NOT_FOUND')
    ranked=await rank_questions(db,p,s); await db.commit()
    return [{'question_id':q.id,'score':score,'reason_codes':reasons,'question':qout(q),
             'signals':{'capability':sig.capability_signal,'evidence_gap':sig.evidence_gap_signal,'opportunity':sig.opportunity_signal,'need':sig.need_signal,'risk':sig.risk_signal},
             'context_refs':sig.context_refs} for score,q,reasons,sig in ranked[:20]]

@router.get('/questions/knowledge',response_model=list[dict])
async def question_knowledge(db:AsyncSession=Depends(get_db),principal:Principal=Depends(require_reviewer)):
    from ...models import CINQuestionKnowledgeLink
    rows=(await db.scalars(select(CINQuestionKnowledgeLink).order_by(CINQuestionKnowledgeLink.relevance_score.desc()).limit(200))).all()
    return [{'question_id':r.question_id,'concept_key':r.concept_key,'concept_type':r.concept_type,'entity_ref':r.entity_ref,'evidence_state':r.evidence_state,'relevance_score':r.relevance_score} for r in rows]
