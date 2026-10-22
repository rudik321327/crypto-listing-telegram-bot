import asyncio
import logging
from datetime import datetime, timezone

from curl_cffi.requests import AsyncSession

from .extract import apply_extraction, is_listing
from .models import Announcement
from .parsers import PARSERS, BaseParser
from .storage import Storage

logger = logging.getLogger(__name__)

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)


class Collector:
    def __init__(self, session: AsyncSession, storage: Storage) -> None:
        self.storage = storage
        self.parsers: list[BaseParser] = [cls(session) for cls in PARSERS]
        self._lock = asyncio.Lock()

    async def collect(self) -> tuple[list[Announcement], dict[str, str]]:
        async with self._lock:
            results = await asyncio.gather(*(self._fetch(parser) for parser in self.parsers))
            fresh: list[Announcement] = []
            errors: dict[str, str] = {}
            for parser, (items, error) in zip(self.parsers, results):
                if error:
                    errors[parser.name] = error
                    continue
                fresh.extend(await self._process(parser, items))
            fresh.sort(key=lambda item: item.published_at or _EPOCH)
            return fresh, errors

    async def _fetch(self, parser: BaseParser) -> tuple[list[Announcement], str | None]:
        try:
            items = await parser.fetch()
            logger.info("%s: fetched %d announcements", parser.name, len(items))
            return items, None
        except Exception as exc:
            logger.warning("%s: fetch failed: %r", parser.name, exc)
            return [], repr(exc)

    async def _process(self, parser: BaseParser, items: list[Announcement]) -> list[Announcement]:
        items = [item for item in items if item.title and is_listing(item.title)]
        known = await self.storage.known_uids([item.uid for item in items])
        fresh = [item for item in items if item.uid not in known]
        seeded = await self.storage.is_seeded(parser.name)
        if seeded and fresh:
            fresh = list(await asyncio.gather(*(parser.enrich(item) for item in fresh)))
        fresh = [apply_extraction(item) for item in fresh]
        await self.storage.save(fresh)
        if not seeded:
            if items:
                await self.storage.mark_seeded(parser.name)
            return []
        return fresh
