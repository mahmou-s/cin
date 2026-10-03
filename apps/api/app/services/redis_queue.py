"""Single-attempt Redis delivery; PostgreSQL outbox reconciliation is recovery."""
import json, logging
from redis.asyncio import Redis
from ..config import settings
logger=logging.getLogger('cin.redis'); QUEUE_KEY='cin:outbox:events'
def redis_client()->Redis:
    return Redis.from_url(settings.redis_url,decode_responses=True,socket_connect_timeout=settings.outbox_socket_timeout_seconds,socket_timeout=settings.outbox_socket_timeout_seconds)
async def enqueue_event(event_id:str)->None:
    redis=redis_client()
    try:
        await redis.rpush(QUEUE_KEY,json.dumps({'event_id':event_id},separators=(',',':')))
    finally:
        await redis.aclose()
