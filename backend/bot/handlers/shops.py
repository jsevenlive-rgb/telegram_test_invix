import uuid

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session
from app.models import Shop, User
from app.temporal.client import get_temporal_client
from app.temporal.shared import CreateShopInput
from app.temporal.workflows import CreateShopWorkflow
from bot.keyboards import main_menu
from bot.states import CreateShopStates

router = Router()


async def _list_user_shops(telegram_id: int) -> list[Shop]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return []
        shops = await session.execute(
            select(Shop).where(Shop.owner_id == user.id).order_by(Shop.created_at.desc())
        )
        return list(shops.scalars().all())


@router.message(Command("shop"))
@router.message(F.text == "🏪 Создать магазин")
async def start_create_shop(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateShopStates.waiting_name)
    await message.answer(
        "Как назовём магазин?\nОтправь название одним сообщением."
    )


@router.message(CreateShopStates.waiting_name, F.text)
async def receive_shop_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Название слишком короткое. Попробуй ещё раз.")
        return

    settings = get_settings()
    client = await get_temporal_client()
    handle = await client.start_workflow(
        CreateShopWorkflow.run,
        CreateShopInput(
            telegram_id=message.from_user.id,
            name=name,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        ),
        id=f"create-shop-{message.from_user.id}-{uuid.uuid4().hex[:8]}",
        task_queue=settings.temporal_task_queue,
    )
    result = await handle.result()
    await state.clear()

    await message.answer(
        f"✅ Магазин «{result.name}» создан!\n"
        f"slug: `{result.slug}`\n\n"
        "Теперь нажми «Создать товар» и отправь название + фото в одном сообщении.",
        parse_mode="Markdown",
        reply_markup=main_menu(is_admin=settings.is_admin(message.from_user.id)),
    )


@router.message(Command("myshops"))
@router.message(F.text == "📦 Мои магазины")
async def my_shops(message: Message) -> None:
    shops = await _list_user_shops(message.from_user.id)
    if not shops:
        await message.answer(
            "У тебя пока нет магазинов. Нажми «Создать магазин».",
            reply_markup=main_menu(is_admin=get_settings().is_admin(message.from_user.id)),
        )
        return

    lines = ["Твои магазины:\n"]
    for s in shops:
        lines.append(f"• #{s.id} — {s.name} (`{s.slug}`)")
    await message.answer(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=main_menu(is_admin=get_settings().is_admin(message.from_user.id)),
    )
