from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import get_settings

router = Router()


@router.message(Command("catalog"))
@router.message(F.text.in_({"🛒 Открыть каталог", "Каталог"}))
async def open_catalog(message: Message) -> None:
    settings = get_settings()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть каталог",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )
    await message.answer(
        "У меня есть товар — открой каталог в Mini App 👇",
        reply_markup=kb,
    )
