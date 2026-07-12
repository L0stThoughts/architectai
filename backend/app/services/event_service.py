"""SSE Event service using Redis pub/sub."""
import json
import logging
import time
from typing import AsyncGenerator, List, Optional

logger = logging.getLogger(__name__)


class EventService:
    """Publishes and subscribes to job events via Redis."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        """Lazy-initialize Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
            except Exception as exc:
                logger.warning("Redis unavailable (%s), events will be no-ops", exc)
        return self._redis

    async def publish(self, job_id: str, event_type: str, data: dict) -> None:
        """Publish an event to the job's Redis channel and history list."""
        event = {
            "event_type": event_type,
            "data": data,
            "timestamp": time.time(),
            "job_id": job_id,
        }
        r = await self._get_redis()
        if r is None:
            logger.debug("No Redis — skipping publish for %s/%s", job_id, event_type)
            return
        try:
            payload = json.dumps(event)
            await r.publish(f"job:{job_id}:events", payload)
            await r.rpush(f"job:{job_id}:history", payload)
            await r.ltrim(f"job:{job_id}:history", -500, -1)
        except Exception as exc:
            logger.error("Failed to publish event: %s", exc)

    async def subscribe(self, job_id: str) -> AsyncGenerator[dict, None]:
        """Subscribe to a job's event channel and yield events."""
        r = await self._get_redis()
        if r is None:
            return
        try:
            pubsub = r.pubsub()
            await pubsub.subscribe(f"job:{job_id}:events")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            logger.error("Subscribe error: %s", exc)

    async def get_history(self, job_id: str, limit: int = 100) -> List[dict]:
        """Return last N events from the job's history list."""
        r = await self._get_redis()
        if r is None:
            return []
        try:
            raw = await r.lrange(f"job:{job_id}:history", -limit, -1)
            return [json.loads(item) for item in raw]
        except Exception as exc:
            logger.error("History retrieval error: %s", exc)
            return []
