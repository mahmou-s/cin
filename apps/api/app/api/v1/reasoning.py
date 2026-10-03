from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...models import ReasoningRun
from ...services.reasoning import analyze_opportunity
from ...auth import Principal, require_authenticated

router = APIRouter()

@router.post('/ai/opportunities/{opportunity_id}/analyze')
async def analyze(opportunity_id: UUID, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    try:
        run = await analyze_opportunity(db, opportunity_id)
        return {'id': str(run.id), 'opportunity_id': str(run.opportunity_id), 'engine': run.engine, 'status': run.status, 'result': run.result}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(404, str(e))

@router.get('/ai/opportunities/{opportunity_id}/reasoning')
async def reasoning_history(opportunity_id: UUID, db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(ReasoningRun).where(ReasoningRun.opportunity_id == opportunity_id).order_by(ReasoningRun.created_at.desc()))
    return {'items': [
        {'id': str(x.id), 'engine': x.engine, 'status': x.status, 'actor': x.actor, 'created_at': x.created_at.isoformat(), 'result': x.result}
        for x in rows.all()
    ]}
