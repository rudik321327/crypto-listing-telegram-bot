import json
import os
from datetime import datetime, timezone

import aiosqlite

from .models import Announcement

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscribers (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS announcements (
    uid TEXT PRIMARY KEY,
    exchange TEXT NOT NULL,
    payload TEXT NOT NULL,
    published_at TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
    exchange TEXT PRIMARY KEY,
    seeded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_announcements_created ON announcements (created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, path: str) -> None:
        self.path = path
        self._db: aiosqlite.Connection | None = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Storage is not initialized")
        return self._db

    async def init(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._db = await aiosqlite.connect(self.path)
        await self.db.executescript(SCHEMA)
        await self.db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def add_subscriber(self, user_id: int, username: str | None) -> bool:
        cursor = await self.db.execute(
            "INSERT OR IGNORE INTO subscribers (user_id, username, created_at) VALUES (?, ?, ?)",
            (user_id, username, _now()),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def remove_subscriber(self, user_id: int) -> bool:
        cursor = await self.db.execute("DELETE FROM subscribers WHERE user_id = ?", (user_id,))
        await self.db.commit()
        return cursor.rowcount > 0

    async def subscribers(self) -> list[int]:
        async with self.db.execute("SELECT user_id FROM subscribers") as cursor:
            return [row[0] for row in await cursor.fetchall()]

    async def is_seeded(self, exchange: str) -> bool:
        async with self.db.execute("SELECT 1 FROM sources WHERE exchange = ?", (exchange,)) as cursor:
            return await cursor.fetchone() is not None

    async def mark_seeded(self, exchange: str) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO sources (exchange, seeded_at) VALUES (?, ?)", (exchange, _now())
        )
        await self.db.commit()

    async def known_uids(self, uids: list[str]) -> set[str]:
        if not uids:
            return set()
        placeholders = ",".join("?" for _ in uids)
        query = f"SELECT uid FROM announcements WHERE uid IN ({placeholders})"
        async with self.db.execute(query, uids) as cursor:
            return {row[0] for row in await cursor.fetchall()}

    async def save(self, items: list[Announcement]) -> None:
        if not items:
            return
        now = _now()
        await self.db.executemany(
            "INSERT OR IGNORE INTO announcements (uid, exchange, payload, published_at, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (
                    item.uid,
                    item.exchange,
                    json.dumps(item.to_dict(), ensure_ascii=False),
                    item.published_at.isoformat() if item.published_at else None,
                    now,
                )
                for item in items
            ],
        )
        await self.db.commit()

    async def get(self, uid: str) -> Announcement | None:
        async with self.db.execute("SELECT payload FROM announcements WHERE uid = ?", (uid,)) as cursor:
            row = await cursor.fetchone()
        return Announcement.from_dict(json.loads(row[0])) if row else None

    async def latest(self, limit: int = 10) -> list[Announcement]:
        query = (
            "SELECT payload FROM announcements "
            "ORDER BY COALESCE(published_at, created_at) DESC LIMIT ?"
        )
        async with self.db.execute(query, (limit,)) as cursor:
            return [Announcement.from_dict(json.loads(row[0])) for row in await cursor.fetchall()]
