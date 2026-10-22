from ..models import Announcement, from_millis
from .base import BaseParser

URL = "https://api.bitget.com/api/v2/public/annoucements"


class BitgetParser(BaseParser):
    name = "Bitget"

    async def fetch(self) -> list[Announcement]:
        data = await self.get_json(URL, params={"language": "en_US", "annType": "coin_listings"})
        items = []
        for entry in data.get("data") or []:
            ann_id = entry.get("annId")
            if not ann_id:
                continue
            items.append(
                Announcement(
                    exchange=self.name,
                    external_id=str(ann_id),
                    title=(entry.get("annTitle") or "").strip(),
                    url=entry.get("annUrl") or f"https://www.bitget.com/support/articles/{ann_id}",
                    published_at=from_millis(entry.get("cTime")),
                    text=(entry.get("annDesc") or "").strip(),
                )
            )
        return items
