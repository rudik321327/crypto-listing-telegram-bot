import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> frozenset[int]:
    return frozenset(int(part) for part in raw.replace(" ", "").split(",") if part)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_token: str
    api_host: str
    api_port: int
    db_path: str
    allowed_user_ids: frozenset[int]
    request_timeout: int
    proxy: str | None


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    return Settings(
        bot_token=bot_token,
        api_token=os.getenv("API_TOKEN", "").strip(),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8080")),
        db_path=os.getenv("DB_PATH", "data/listings.db"),
        allowed_user_ids=_parse_ids(os.getenv("ALLOWED_USER_IDS", "")),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "20")),
        proxy=os.getenv("HTTP_PROXY_URL") or None,
    )
