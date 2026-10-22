import re

from .models import Announcement

_MONTHS = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
_UTC = r"\(?\s*UTC\s*(?:[+-]\s*\d{1,2})?\s*\)?"

_TIME_PATTERNS = [
    re.compile(rf"\d{{4}}[-/.]\d{{1,2}}[-/.]\d{{1,2}}[ ,T]+(?:at\s+)?\d{{1,2}}:\d{{2}}(?::\d{{2}})?\s*(?:[AP]M)?\s*{_UTC}", re.I),
    re.compile(rf"{_MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}},?\s+(?:at\s+)?\d{{1,2}}:\d{{2}}(?::\d{{2}})?\s*(?:[AP]M)?\s*{_UTC}", re.I),
    re.compile(rf"\d{{1,2}}\s+{_MONTHS}\s+\d{{4}},?\s+(?:at\s+)?\d{{1,2}}:\d{{2}}(?::\d{{2}})?\s*(?:[AP]M)?\s*{_UTC}", re.I),
    re.compile(rf"\d{{1,2}}:\d{{2}}(?::\d{{2}})?\s*(?:[AP]M)?\s*{_UTC},?\s+(?:on\s+)?{_MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?", re.I),
]

_TICKER_PAREN = re.compile(r"\(([A-Z0-9]{2,15})\)")
_TICKER_PAIR = re.compile(r"\b([A-Z0-9]{2,15})[/_-]?(?:USDT|USDC|USD|BTC|ETH|EUR|TRY)\b")

_STOP_TICKERS = {
    "UTC", "USDT", "USDC", "USD", "BTC", "ETH", "EUR", "TRY", "API", "APR", "APY",
    "HODLER", "NEW", "VIP", "ID", "AM", "PM", "KYC", "AI", "OKX", "MEXC", "GATE",
}

_INCLUDE = (
    "list", "launch", "trading pair", "pre-market", "premarket", "debut",
    "innovation zone", "new spot", "new futures", "new perpetual", "will add", "airdrop",
)
_EXCLUDE = ("delist", "removal", "will remove", "cease", "suspend", "maintenance")


def is_listing(title: str) -> bool:
    lowered = title.lower()
    if any(word in lowered for word in _EXCLUDE):
        return False
    return any(word in lowered for word in _INCLUDE)


def find_tickers(text: str) -> list[str]:
    found: list[str] = []
    for pattern in (_TICKER_PAREN, _TICKER_PAIR):
        for match in pattern.findall(text):
            if match not in _STOP_TICKERS and not match.isdigit() and match not in found:
                found.append(match)
    return found[:10]


def find_listing_time(text: str) -> str | None:
    for pattern in _TIME_PATTERNS:
        match = pattern.search(text)
        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip(" ,")
    return None


def apply_extraction(item: Announcement) -> Announcement:
    head = f"{item.title}\n{item.text[:600]}"
    item.tickers = find_tickers(item.title) or find_tickers(head)
    item.listing_time = find_listing_time(head) or find_listing_time(item.text)
    return item
