import re
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from ..config import Settings
from ..models import Announcement

IMPERSONATE = "chrome124"
HEADERS = {"Accept-Language": "en-US,en;q=0.9"}
MAX_TEXT = 4000


def create_http_session(settings: Settings) -> AsyncSession:
    return AsyncSession(
        impersonate=IMPERSONATE,
        headers=HEADERS,
        timeout=settings.request_timeout,
        proxy=settings.proxy,
    )


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg"]):
        tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body or soup
    return re.sub(r"\s+", " ", root.get_text(" ", strip=True))[:MAX_TEXT]


class BaseParser:
    name = ""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def fetch(self) -> list[Announcement]:
        raise NotImplementedError

    async def enrich(self, item: Announcement) -> Announcement:
        try:
            item.text = (item.text + " " + html_to_text(await self.get_text(item.url))).strip()[:MAX_TEXT]
        except Exception:
            pass
        return item

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        response = await self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.json()

    async def get_text(self, url: str, **kwargs: Any) -> str:
        response = await self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.text
