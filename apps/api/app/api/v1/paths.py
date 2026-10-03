from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...services.path_reasoning import discover_paths, analyze_path
from ...auth import Principal, require_authenticated

router = APIRouter()

@router.get('/reasoning/paths')
async def paths(limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    items = await discover_paths(db, limit)
    return {'count': len(items), 'items': items}

@router.post('/reasoning/paths/analyze')
async def analyze(payload: dict, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    try:
        ids = [UUID(x) for x in payload.get('assertion_ids', [])]
        if len(ids) < 3:
            raise ValueError('AT_LEAST_3_ASSERTIONS_REQUIRED')
        result = await analyze_path(db, ids, principal.subject)
        return result
    except (ValueError, AttributeError) as e:
        raise HTTPException(400, str(e))
