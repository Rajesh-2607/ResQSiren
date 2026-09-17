"""Thin async Redis pub/sub wrapper shared by every service."""
import asyncio
import json
import logging
from typing import Any, AsyncIterator, Callable, Coroutine

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger("resq.bus")


class EventBus:
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        self._redis = redis.from_url(self._redis_url, decode_responses=True)
        await self._redis.ping()

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    @property
    def redis(self) -> redis.Redis:
        assert self._redis is not None, "EventBus.connect() must be called first"
        return self._redis

    async def publish(self, channel: str, event: BaseModel) -> None:
        payload = event.model_dump(mode="json")
        await self.redis.publish(channel, json.dumps(payload))
        logger.info("published %s -> %s", channel, payload)

    async def subscribe(self, *channels: str) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*channels)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                except (TypeError, json.JSONDecodeError):
                    logger.warning("dropping malformed event on %s", message["channel"])
                    continue
                yield message["channel"], data
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.aclose()

    def run_subscriber(
        self,
        channel: str,
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> asyncio.Task:
        """Fire-and-forget background task that dispatches each message on `channel` to `handler`."""

        async def _loop() -> None:
            async for _, data in self.subscribe(channel):
                try:
                    await handler(data)
                except Exception:
                    logger.exception("handler failed for event on %s", channel)

        return asyncio.create_task(_loop())
