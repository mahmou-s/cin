from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...models import Scenario
from ...services.scenarios import generate_scenario, serialize_scenario
from ...auth import Principal, require_authenticated

router=APIRouter()
class ScenarioRequest(BaseModel):
    goal: str = Field(min_length=5, max_length=1000)
    requested_codes: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=10)

@router.post('/scenarios/generate')
async def generate(payload: ScenarioRequest, db: AsyncSession=Depends(get_db), principal: Principal=Depends(require_authenticated)):
    try:
        items=await generate_scenario(db,payload.goal,payload.requested_codes,payload.limit)
        return {"count":len(items),"items":[await serialize_scenario(db,s.id) for s,_ in items]}
    except ValueError as e:
        await db.rollback(); raise HTTPException(400,str(e))

@router.get('/scenarios')
async def list_scenarios(db: AsyncSession=Depends(get_db)):
    rows=(await db.scalars(select(Scenario).order_by(Scenario.created_at.desc()).limit(50))).all()
    items=[]
    for s in rows:
        items.append(await serialize_scenario(db, s.id))
    return {"count":len(items),"items":items}

@router.get('/scenarios/{scenario_id}')
async def get_scenario(scenario_id: UUID, db: AsyncSession=Depends(get_db)):
    try: return await serialize_scenario(db,scenario_id)
    except ValueError as e: raise HTTPException(404,str(e))
