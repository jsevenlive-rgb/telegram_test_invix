from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.config import get_settings
from bot.keyboards import main_menu

router = Router()

GREETING = "У меня есть товар"


@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    await message.answer(
        GREETING,
        reply_markup=main_menu(is_admin=settings.is_admin(message.from_user.id)),
    )
