import re

from bs4 import BeautifulSoup

from ..models import Announcement
from .base import BaseParser

BASE_URL = "https://www.mexc.com"
LIST_URL = f"{BASE_URL}/announcements/new-listings"
ARTICLE_RE = re.compile(r"^/announcements/article/([\w-]*?-?(\d{8,}))$")


class MexcParser(BaseParser):
    name = "MEXC"

    async def fetch(self) -> list[Announcement]:
        soup = BeautifulSoup(await self.get_text(LIST_URL), "html.parser")
        items: dict[str, Announcement] = {}
        for link in soup.find_all("a", href=ARTICLE_RE):
            match = ARTICLE_RE.match(link["href"])
            title = " ".join(link.get_text(" ", strip=True).split())
            if not match or not title:
                continue
            article_id = match.group(2)
            if article_id in items:
                continue
            items[article_id] = Announcement(
                exchange=self.name,
                external_id=article_id,
                title=title,
                url=f"{BASE_URL}{link['href']}",
            )
        return list(items.values())
