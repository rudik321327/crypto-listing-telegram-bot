import json
import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from ..models import Announcement
from .base import MAX_TEXT, BaseParser, html_to_text

BASE_URL = "https://www.gate.com"
LIST_URL = f"{BASE_URL}/en/announcements/newlisted"
ARTICLE_RE = re.compile(r"/announcements/article/(\d+)")


def _article_url(article_id: str) -> str:
    return f"{BASE_URL}/en/announcements/article/{article_id}"


def _from_seconds(value: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


class GateParser(BaseParser):
    name = "Gate"

    async def fetch(self) -> list[Announcement]:
        soup = BeautifulSoup(await self.get_text(LIST_URL), "html.parser")
        return self._from_next_data(soup) or self._from_links(soup)

    def _from_next_data(self, soup: BeautifulSoup) -> list[Announcement]:
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return []
        try:
            entries = json.loads(script.string)["props"]["pageProps"]["listData"]["list"]
        except (KeyError, TypeError, ValueError):
            return []
        items = []
        for entry in entries:
            article_id = str(entry.get("id") or "")
            if not article_id:
                continue
            items.append(
                Announcement(
                    exchange=self.name,
                    external_id=article_id,
                    title=(entry.get("title") or "").strip(),
                    url=_article_url(article_id),
                    published_at=_from_seconds(entry.get("release_timestamp")),
                    text=(entry.get("brief") or "").strip(),
                )
            )
        return items

    def _from_links(self, soup: BeautifulSoup) -> list[Announcement]:
        items: dict[str, Announcement] = {}
        for link in soup.find_all("a", href=ARTICLE_RE):
            match = ARTICLE_RE.search(link["href"])
            title_node = link.find("div") or link
            title = " ".join(title_node.get_text(" ", strip=True).split())
            if not match or not title or match.group(1) in items:
                continue
            items[match.group(1)] = Announcement(
                exchange=self.name,
                external_id=match.group(1),
                title=title,
                url=_article_url(match.group(1)),
            )
        return list(items.values())

    async def enrich(self, item: Announcement) -> Announcement:
        try:
            html = await self.get_text(item.url)
        except Exception:
            return item
        heading = BeautifulSoup(html, "html.parser").find("h1")
        if item.title.endswith("...") and heading and heading.get_text(strip=True):
            item.title = " ".join(heading.get_text(" ", strip=True).split())
        item.text = (item.text + " " + html_to_text(html)).strip()[:MAX_TEXT]
        return item
