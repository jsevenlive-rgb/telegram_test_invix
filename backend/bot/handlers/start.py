from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session
from app.models import Shop, User
from bot.keyboards import main_menu

router = Router()


async def user_has_shops(telegram_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return False
        shops = await session.execute(select(Shop.id).where(Shop.owner_id == user.id).limit(1))
        return shops.scalar_one_or_none() is not None


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    has_shops = await user_has_shops(message.from_user.id)
    is_owner = has_shops or settings.is_admin(message.from_user.id)

    text = (
        "👋 Привет!\n\n"
        "У меня есть товар — открой каталог в Mini App и посмотри витрину.\n\n"
        "Любой желающий может создать свой магазин и разместить товары на витрине.\n\n"
        "• «Открыть каталог» — публичная лента товаров всех магазинов\n"
        "• «Создать магазин» — открыть свою витрину\n"
    )
    if is_owner:
        text += "• «Создать товар» — название + фото в одном сообщении\n"

    await message.answer(text, reply_markup=main_menu(is_owner=is_owner))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/start — главное меню\n"
        "/shop — создать магазин\n"
        "/product — создать товар (нужен магазин)\n"
        "/myshops — мои магазины\n"
        "/catalog — открыть каталог"
    )
