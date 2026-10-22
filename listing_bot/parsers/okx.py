from ..models import Announcement, from_millis
from .base import BaseParser

URL = "https://www.okx.com/api/v5/support/announcements"


class OkxParser(BaseParser):
    name = "OKX"

    async def fetch(self) -> list[Announcement]:
        data = await self.get_json(URL, params={"annType": "announcements-new-listings", "page": 1})
        items = []
        for block in data.get("data") or []:
            for detail in block.get("details") or []:
                url = detail.get("url") or ""
                if not url:
                    continue
                items.append(
                    Announcement(
                        exchange=self.name,
                        external_id=url.rstrip("/").rsplit("/", 1)[-1],
                        title=detail.get("title", "").strip(),
                        url=url,
                        published_at=from_millis(detail.get("pTime")),
                    )
                )
        return items
