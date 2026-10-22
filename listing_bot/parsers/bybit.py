from ..models import Announcement, from_millis
from .base import BaseParser

URL = "https://api.bybit.com/v5/announcements/index"


class BybitParser(BaseParser):
    name = "Bybit"

    async def fetch(self) -> list[Announcement]:
        params = {"locale": "en-US", "type": "new_crypto", "page": 1, "limit": 20}
        data = await self.get_json(URL, params=params)
        items = []
        for entry in (data.get("result") or {}).get("list") or []:
            url = entry.get("url") or ""
            if not url:
                continue
            items.append(
                Announcement(
                    exchange=self.name,
                    external_id=url.rstrip("/").rsplit("/", 1)[-1],
                    title=entry.get("title", "").strip(),
                    url=url,
                    published_at=from_millis(entry.get("publishTime") or entry.get("dateTimestamp")),
                    text=(entry.get("description") or "").strip(),
                )
            )
        return items
