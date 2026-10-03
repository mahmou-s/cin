from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...auth import Principal, require_steward
from ...db import get_db
from ...models import SyncEvent
from ...services.redis_queue import enqueue_event
router=APIRouter()
@router.post('/outbox/{event_id}/replay')
async def replay(event_id:UUID, db:AsyncSession=Depends(get_db), principal:Principal=Depends(require_steward)):
    event=await db.get(SyncEvent,event_id)
    if not event: raise HTTPException(404,'OUTBOX_EVENT_NOT_FOUND')
    if event.status!='DEAD_LETTER': raise HTTPException(409,'OUTBOX_EVENT_NOT_DEAD_LETTER')
    event.status='PENDING'; event.attempts=0; event.next_attempt_at=None; event.last_error='STEWARD_REPLAY'; event.processing_started_at=None
    await db.commit()
    try: await enqueue_event(str(event.id))
    except Exception: pass
    return {'id':str(event.id),'status':'PENDING','actor':principal.subject}
