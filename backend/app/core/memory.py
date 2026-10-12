import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class AgentMemoryStore:
    """Agent memory: shared state snapshots, per-job event logs and live event fan-out.

    * Redis backend (USE_IN_MEMORY_REDIS=false): state and event logs are stored in Redis
      with a TTL, so they survive restarts and are shared by multiple workers.
    * In-memory backend: used when Redis is disabled or unreachable (automatic fallback).
    Live subscriber queues (SSE/polling) are always process-local.
    """

    def __init__(self):
        self._state: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        self._redis = None
        self._redis_checked = False

    # ----------------------------------------------------------------- redis
    async def _get_redis(self):
        if settings.USE_IN_MEMORY_REDIS:
            return None
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.ping()
            self._redis = client
            logger.info("Connected to Redis for agent memory.")
        except Exception as exc:
            logger.warning("Redis unavailable (%s); using in-memory agent memory.", exc)
            self._redis = None
        return self._redis

    async def backend_name(self) -> str:
        return "redis" if await self._get_redis() is not None else "memory"

    @staticmethod
    def _dumps(value: Any) -> str:
        return json.dumps(value, default=str)

    # ----------------------------------------------------------------- state
    async def save_state(self, key: str, data: Dict[str, Any]):
        async with self._lock:
            self._state[key] = {"data": data, "updated_at": datetime.now(timezone.utc).isoformat()}
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.set(f"compliance:state:{key}", self._dumps(data), ex=settings.REDIS_TTL_SECONDS)
            except Exception as exc:
                logger.warning("Redis save_state failed: %s", exc)

    async def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        redis = await self._get_redis()
        if redis is not None:
            try:
                raw = await redis.get(f"compliance:state:{key}")
                if raw:
                    return json.loads(raw)
            except Exception as exc:
                logger.warning("Redis get_state failed: %s", exc)
        async with self._lock:
            entry = self._state.get(key)
            return entry["data"] if entry else None

    # ---------------------------------------------------------------- events
    async def append_event(self, job_id: str, event_data: Dict[str, Any]):
        event_data = dict(event_data)
        event_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        async with self._lock:
            self._events.setdefault(job_id, []).append(event_data)
            subscribers = list(self._subscribers.get(job_id, []))
        for q in subscribers:
            await q.put(event_data)
        redis = await self._get_redis()
        if redis is not None:
            try:
                key = f"compliance:events:{job_id}"
                await redis.rpush(key, self._dumps(event_data))
                await redis.expire(key, settings.REDIS_TTL_SECONDS)
            except Exception as exc:
                logger.warning("Redis append_event failed: %s", exc)

    async def get_events(self, job_id: str) -> List[Dict[str, Any]]:
        redis = await self._get_redis()
        if redis is not None:
            try:
                raw = await redis.lrange(f"compliance:events:{job_id}", 0, -1)
                if raw:
                    return [json.loads(item) for item in raw]
            except Exception as exc:
                logger.warning("Redis get_events failed: %s", exc)
        async with self._lock:
            return list(self._events.get(job_id, []))

    # ------------------------------------------------------------ subscribers
    async def subscribe(self, job_id: str) -> asyncio.Queue:
        async with self._lock:
            q: asyncio.Queue = asyncio.Queue()
            self._subscribers.setdefault(job_id, []).append(q)
            return q

    async def unsubscribe(self, job_id: str, q: asyncio.Queue):
        async with self._lock:
            if job_id in self._subscribers and q in self._subscribers[job_id]:
                self._subscribers[job_id].remove(q)


memory_store = AgentMemoryStore()
