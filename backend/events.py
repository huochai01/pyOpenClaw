from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any


class SessionEventBroker:
    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue]] = defaultdict(set)

    async def subscribe(self, session_id: str):
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[session_id].add(queue)
        try:
            while True:
                item = await queue.get()
                yield item
        finally:
            subscribers = self._queues.get(session_id)
            if subscribers is not None:
                subscribers.discard(queue)
                if not subscribers:
                    self._queues.pop(session_id, None)

    async def publish(self, session_id: str, event: str, data: Any) -> None:
        subscribers = list(self._queues.get(session_id, set()))
        if not subscribers:
            return
        payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        for queue in subscribers:
            await queue.put(payload)
