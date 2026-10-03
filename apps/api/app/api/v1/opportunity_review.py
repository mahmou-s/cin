from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...services.opportunity_review import queue, review
from ...auth import Principal, require_reviewer
router=APIRouter()
class ReviewBody(BaseModel):
    decision: str
    note: str | None = None
@router.get('/civilizational-opportunities/review-queue')
async def get_queue(db:AsyncSession=Depends(get_db)): return {'items':await queue(db)}
@router.post('/civilizational-opportunities/{opportunity_id}/review')
async def post_review(opportunity_id:UUID, body:ReviewBody, db:AsyncSession=Depends(get_db), principal:Principal=Depends(require_reviewer)):
    try: result=await review(db,opportunity_id,body.decision.upper(),principal.subject,body.note)
    except ValueError as e: raise HTTPException(400,str(e))
    if not result: raise HTTPException(404,'Opportunity not found')
    return result
