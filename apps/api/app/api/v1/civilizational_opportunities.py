from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...services.civilizational_opportunities import discover

router=APIRouter()

@router.get('/civilizational-opportunities/discover')
async def discover_opportunities(limit:int=Query(20,ge=1,le=100), db:AsyncSession=Depends(get_db)):
    items=await discover(db,limit)
    return {'items':items,'count':len(items),'model':'capability-to-opportunity-path'}
