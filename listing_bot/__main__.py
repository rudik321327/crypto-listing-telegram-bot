import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from .api import create_app
from .bot import COMMANDS, Notifier, create_router
from .collector import Collector
from .config import load_settings
from .parsers import create_http_session
from .storage import Storage


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    storage = Storage(settings.db_path)
    await storage.init()

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router())
    dispatcher["db"] = storage
    dispatcher["settings"] = settings

    async with create_http_session(settings) as session:
        collector = Collector(session, storage)
        app = create_app(settings, storage, collector, Notifier(bot, storage))
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, settings.api_host, settings.api_port).start()
        logging.getLogger(__name__).info("API listening on %s:%s", settings.api_host, settings.api_port)
        try:
            await bot.set_my_commands(COMMANDS)
            await dispatcher.start_polling(bot)
        finally:
            await runner.cleanup()
            await storage.close()
            await bot.session.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
