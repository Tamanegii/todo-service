import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class _SessionBuffer:
    messages: list[str] = field(default_factory=list)
    timer: asyncio.Task | None = None


class MessageAggregator:
    def __init__(self, on_complete: Callable[[str, str], Awaitable[None]]):
        self._sessions: dict[str, _SessionBuffer] = {}
        self._window = settings.aggregation_window_seconds
        self._on_complete = on_complete

    async def add_message(self, session_id: str, text: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = _SessionBuffer()

        buf = self._sessions[session_id]
        buf.messages.append(text)

        if buf.timer and not buf.timer.done():
            buf.timer.cancel()

        buf.timer = asyncio.create_task(self._flush_after_delay(session_id))

    async def _flush_after_delay(self, session_id: str) -> None:
        await asyncio.sleep(self._window)
        buf = self._sessions.pop(session_id, None)
        if not buf:
            return
        aggregated = "\n".join(buf.messages)
        logger.info("Session %s aggregated: %s", session_id, aggregated)
        try:
            await self._on_complete(session_id, aggregated)
        except Exception:
            logger.exception("Failed to process aggregated message for session %s", session_id)
