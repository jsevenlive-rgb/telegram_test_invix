import uuid

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session
from app.models import Shop, User
from app.temporal.client import get_temporal_client
from app.temporal.shared import CreateProductInput, CreateShopInput
from app.temporal.workflows import CreateProductWorkflow, CreateShopWorkflow
from bot.keyboards import main_menu, shops_inline
from bot.states import CreateProductStates

router = Router()


async def _user_shops(telegram_id: int) -> list[dict]:
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
        return [
            {"id": s.id, "name": s.name, "slug": s.slug}
            for s in shops.scalars().all()
        ]


async def _ensure_admin_shop(message: Message) -> list[dict]:
    """Admin can place products immediately — auto-create a default shop via Temporal."""
    settings = get_settings()
    client = await get_temporal_client()
    name = f"Магазин {message.from_user.first_name or message.from_user.id}"
    handle = await client.start_workflow(
        CreateShopWorkflow.run,
        CreateShopInput(
            telegram_id=message.from_user.id,
            name=name,
            description="Автосоздан для администратора",
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        ),
        id=f"create-shop-admin-{message.from_user.id}-{uuid.uuid4().hex[:8]}",
        task_queue=settings.temporal_task_queue,
    )
    result = await handle.result()
    return [{"id": result.shop_id, "name": result.name, "slug": result.slug}]


@router.message(Command("product"))
@router.message(F.text == "➕ Создать товар")
async def start_create_product(message: Message, state: FSMContext) -> None:
    shops = await _user_shops(message.from_user.id)
    settings = get_settings()
    is_admin = settings.is_admin(message.from_user.id)

    if not shops and not is_admin:
        await message.answer(
            "Сначала создай магазин — кнопка «Создать магазин».",
            reply_markup=main_menu(is_owner=False),
        )
        return

    if not shops and is_admin:
        await message.answer("Создаю витрину для администратора…")
        shops = await _ensure_admin_shop(message)

    if len(shops) == 1:
        await state.update_data(shop_id=shops[0]["id"])
        await state.set_state(CreateProductStates.waiting_photo)
        await message.answer(
            f"Магазин: «{shops[0]['name']}»\n\n"
            "Отправь одно сообщение: фото товара + название в подписи (caption).\n"
            "Пример: прикрепи фото и напиши «Кроссовки Nike Air»."
        )
        return

    await state.set_state(CreateProductStates.choosing_shop)
    await message.answer(
        "Выбери магазин для товара:",
        reply_markup=shops_inline(shops),
    )


@router.callback_query(CreateProductStates.choosing_shop, F.data.startswith("pick_shop:"))
async def pick_shop(callback: CallbackQuery, state: FSMContext) -> None:
    shop_id = int(callback.data.split(":")[1])
    await state.update_data(shop_id=shop_id)
    await state.set_state(CreateProductStates.waiting_photo)
    await callback.message.answer(
        "Отправь одно сообщение: фото товара + название в подписи (caption)."
    )
    await callback.answer()


@router.message(CreateProductStates.waiting_photo, F.photo)
async def receive_product_photo(message: Message, state: FSMContext) -> None:
    title = (message.caption or "").strip()
    if not title:
        await message.answer(
            "Нужно название в подписи к фото.\n"
            "Отправь фото ещё раз и укажи название в caption."
        )
        return

    data = await state.get_data()
    shop_id = data.get("shop_id")
    if not shop_id:
        await state.clear()
        await message.answer("Сессия сброшена. Начни снова: «Создать товар».")
        return

    photo = message.photo[-1]
    settings = get_settings()
    client = await get_temporal_client()
    handle = await client.start_workflow(
        CreateProductWorkflow.run,
        CreateProductInput(
            shop_id=shop_id,
            title=title,
            telegram_file_id=photo.file_id,
        ),
        id=f"create-product-{shop_id}-{uuid.uuid4().hex[:8]}",
        task_queue=settings.temporal_task_queue,
    )
    result = await handle.result()
    await state.clear()

    await message.answer(
        f"✅ Товар «{result.title}» размещён на витрине!\n"
        f"Он уже в публичном каталоге Mini App.",
        reply_markup=main_menu(is_owner=True),
    )


@router.message(CreateProductStates.waiting_photo)
async def waiting_photo_wrong(message: Message) -> None:
    await message.answer(
        "Жду фото с названием в подписи.\n"
        "Отправь изображение и caption одним сообщением."
    )
