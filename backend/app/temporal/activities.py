from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy import select
from temporalio import activity

from app.config import get_settings
from app.database import async_session
from app.models import Product, Shop, User
from app.services.s3 import upload_bytes
from app.services.slug import slugify
from app.temporal.shared import (
    CreateProductInput,
    CreateProductResult,
    CreateShopInput,
    CreateShopResult,
    ProductRecord,
)


def _parse_price(price: str | None) -> Decimal | None:
    if price is None or not str(price).strip():
        return None
    try:
        return Decimal(str(price).strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid price: {price}") from exc


@activity.defn
async def ensure_user_and_create_shop(data: CreateShopInput) -> CreateShopResult:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == data.telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=data.telegram_id,
                username=data.username,
                first_name=data.first_name,
            )
            session.add(user)
            await session.flush()
        else:
            if data.username is not None:
                user.username = data.username
            if data.first_name is not None:
                user.first_name = data.first_name

        shop = Shop(
            owner_id=user.id,
            name=data.name.strip(),
            description=data.description,
            slug=slugify(data.name),
        )
        session.add(shop)
        await session.commit()
        await session.refresh(shop)

        return CreateShopResult(shop_id=shop.id, slug=shop.slug, name=shop.name)


@activity.defn
async def fetch_and_store_product_image(data: CreateProductInput) -> tuple[str, str]:
    """Download photo from Telegram and upload to MinIO in one activity (no large payloads in workflow)."""
    settings = get_settings()
    client_kwargs: dict = {"timeout": 60.0}
    if settings.telegram_proxy_url:
        client_kwargs["proxy"] = settings.telegram_proxy_url
    async with httpx.AsyncClient(**client_kwargs) as client:
        meta = await client.get(
            f"https://api.telegram.org/bot{settings.bot_token}/getFile",
            params={"file_id": data.telegram_file_id},
        )
        meta.raise_for_status()
        payload = meta.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram getFile failed: {payload}")
        file_path = payload["result"]["file_path"]
        content = await client.get(
            f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
        )
        content.raise_for_status()
        image_bytes = content.content

    return upload_bytes(
        image_bytes,
        content_type="image/jpeg",
        filename="photo.jpg",
        prefix=f"products/shop_{data.shop_id}",
    )


@activity.defn
async def save_product(record: ProductRecord) -> CreateProductResult:
    async with async_session() as session:
        shop = await session.get(Shop, record.shop_id)
        if shop is None:
            raise ValueError(f"Shop {record.shop_id} not found")

        product = Product(
            shop_id=record.shop_id,
            title=record.title.strip(),
            description=record.description,
            price=_parse_price(record.price),
            image_key=record.image_key,
            image_url=record.image_url,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)

        return CreateProductResult(
            product_id=product.id,
            title=product.title,
            image_url=product.image_url,
            shop_id=product.shop_id,
        )


@activity.defn
async def get_user_shops(telegram_id: int) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return []

        shops_result = await session.execute(
            select(Shop).where(Shop.owner_id == user.id).order_by(Shop.created_at.desc())
        )
        shops = shops_result.scalars().all()
        return [
            {"id": s.id, "name": s.name, "slug": s.slug, "description": s.description}
            for s in shops
        ]
