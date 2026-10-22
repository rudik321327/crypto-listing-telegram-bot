import json
from typing import Any

from ..models import Announcement, from_millis
from .base import MAX_TEXT, BaseParser

LIST_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
NEW_LISTING_CATALOG = 48


def _collect_text(node: Any, out: list[str]) -> None:
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            out.append(node["text"])
        for child in node.get("child", []) or []:
            _collect_text(child, out)
    elif isinstance(node, list):
        for child in node:
            _collect_text(child, out)


class BinanceParser(BaseParser):
    name = "Binance"

    async def fetch(self) -> list[Announcement]:
        params = {"type": 1, "catalogId": NEW_LISTING_CATALOG, "pageNo": 1, "pageSize": 20}
        data = await self.get_json(LIST_URL, params=params)
        items = []
        for catalog in (data.get("data") or {}).get("catalogs") or []:
            for article in catalog.get("articles") or []:
                code = article.get("code")
                if not code:
                    continue
                items.append(
                    Announcement(
                        exchange=self.name,
                        external_id=code,
                        title=article.get("title", "").strip(),
                        url=f"https://www.binance.com/en/support/announcement/{code}",
                        published_at=from_millis(article.get("releaseDate")),
                    )
                )
        return items

    async def enrich(self, item: Announcement) -> Announcement:
        try:
            data = await self.get_json(DETAIL_URL, params={"articleCode": item.external_id})
            body = (data.get("data") or {}).get("body") or ""
            parts: list[str] = []
            _collect_text(json.loads(body) if body.startswith(("{", "[")) else body, parts)
            item.text = " ".join(" ".join(parts).split())[:MAX_TEXT]
        except Exception:
            pass
        return item
