from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.config import get_settings
from bot.handlers.start import GREETING
from bot.keyboards import main_menu

router = Router()


@router.message(StateFilter(None), F.text)
async def any_message(message: Message) -> None:
    """Ordinary messages get the same catalog offer as /start."""
    settings = get_settings()
    await message.answer(
        GREETING,
        reply_markup=main_menu(is_admin=settings.is_admin(message.from_user.id)),
    )
