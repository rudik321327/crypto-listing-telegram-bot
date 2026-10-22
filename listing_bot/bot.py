import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, Message

from .config import Settings
from .formatting import format_announcement
from .models import Announcement
from .parsers import PARSERS
from .storage import Storage

logger = logging.getLogger(__name__)

COMMANDS = [
    BotCommand(command="start", description="Подписаться на листинги"),
    BotCommand(command="stop", description="Отписаться"),
    BotCommand(command="latest", description="Последние объявления"),
    BotCommand(command="status", description="Состояние бота"),
]


def create_router() -> Router:
    router = Router()
    router.message.filter(F.chat.type == "private")

    @router.message(CommandStart())
    async def start(message: Message, db: Storage, settings: Settings) -> None:
        user = message.from_user
        if settings.allowed_user_ids and user.id not in settings.allowed_user_ids:
            await message.answer("Доступ запрещён.")
            return
        added = await db.add_subscriber(user.id, user.username)
        text = "Подписка оформлена." if added else "Вы уже подписаны."
        await message.answer(f"{text} Новые объявления о листингах будут приходить сюда.")

    @router.message(Command("stop"))
    async def stop(message: Message, db: Storage) -> None:
        removed = await db.remove_subscriber(message.from_user.id)
        await message.answer("Подписка отменена." if removed else "Вы не были подписаны.")

    @router.message(Command("latest"))
    async def latest(message: Message, db: Storage) -> None:
        items = await db.latest(5)
        if not items:
            await message.answer("Объявлений пока нет.")
            return
        for item in items:
            await message.answer(format_announcement(item), disable_web_page_preview=True)

    @router.message(Command("status"))
    async def status(message: Message, db: Storage) -> None:
        subscribed = message.from_user.id in await db.subscribers()
        exchanges = ", ".join(parser.name for parser in PARSERS)
        await message.answer(
            f"Подписка: {'активна' if subscribed else 'нет'}\nБиржи: {exchanges}"
        )

    return router


class Notifier:
    def __init__(self, bot: Bot, storage: Storage) -> None:
        self.bot = bot
        self.storage = storage

    async def broadcast(self, item: Announcement) -> int:
        text = format_announcement(item)
        sent = 0
        for user_id in await self.storage.subscribers():
            if await self._send(user_id, text):
                sent += 1
            await asyncio.sleep(0.05)
        return sent

    async def _send(self, user_id: int, text: str) -> bool:
        for _ in range(3):
            try:
                await self.bot.send_message(user_id, text, disable_web_page_preview=True)
                return True
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after)
            except TelegramForbiddenError:
                await self.storage.remove_subscriber(user_id)
                return False
            except TelegramBadRequest as exc:
                logger.warning("Send to %s failed: %s", user_id, exc)
                return False
        return False
