import asyncio
import logging
import sys
from pathlib import Path

# Allow `python -m bot.main` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings
from app.database import init_db
from app.services.s3 import ensure_bucket
from bot.handlers import setup_routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not set")

    await init_db()
    try:
        ensure_bucket()
    except Exception as exc:
        logger.warning("Media storage init deferred: %s", exc)

    # aiogram/python-socks accept socks5://, not socks5h://
    proxy = settings.telegram_proxy_url.replace("socks5h://", "socks5://", 1)
    session = AiohttpSession(proxy=proxy) if proxy else AiohttpSession()
    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())

    logger.info("Bot starting… webapp=%s", settings.webapp_url)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
