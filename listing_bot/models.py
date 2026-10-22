from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Announcement:
    exchange: str
    external_id: str
    title: str
    url: str
    published_at: datetime | None = None
    text: str = ""
    tickers: list[str] = field(default_factory=list)
    listing_time: str | None = None

    @property
    def uid(self) -> str:
        return f"{self.exchange}:{self.external_id}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["uid"] = self.uid
        data["published_at"] = self.published_at.isoformat() if self.published_at else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Announcement":
        published = data.get("published_at")
        return cls(
            exchange=data["exchange"],
            external_id=str(data["external_id"]),
            title=data["title"],
            url=data["url"],
            published_at=datetime.fromisoformat(published) if published else None,
            text=data.get("text") or "",
            tickers=list(data.get("tickers") or []),
            listing_time=data.get("listing_time"),
        )


def from_millis(value: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None
