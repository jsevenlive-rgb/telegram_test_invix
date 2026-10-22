import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio.client import Client

from app.config import get_settings
from app.database import get_db
from app.models import Product, Shop, User
from app.schemas.product import ProductOut
from app.schemas.shop import ShopCreate, ShopOut
from app.temporal.client import get_temporal_client
from app.temporal.shared import CreateShopInput
from app.temporal.workflows import CreateShopWorkflow

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("", response_model=list[ShopOut])
async def list_shops(db: AsyncSession = Depends(get_db)) -> list[Shop]:
    result = await db.execute(select(Shop).order_by(Shop.created_at.desc()))
    return list(result.scalars().all())


@router.get("/by-owner/{telegram_id}", response_model=list[ShopOut])
async def shops_by_owner(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[Shop]:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        return []
    shops = await db.execute(
        select(Shop).where(Shop.owner_id == user.id).order_by(Shop.created_at.desc())
    )
    return list(shops.scalars().all())


@router.get("/{shop_id}", response_model=ShopOut)
async def get_shop(shop_id: int, db: AsyncSession = Depends(get_db)) -> Shop:
    shop = await db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.get("/{shop_id}/products", response_model=list[ProductOut])
async def shop_products(
    shop_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[Product]:
    shop = await db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    result = await db.execute(
        select(Product)
        .where(Product.shop_id == shop_id)
        .order_by(Product.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ShopOut, status_code=201)
async def create_shop(
    payload: ShopCreate,
    db: AsyncSession = Depends(get_db),
) -> Shop:
    """Create shop via Temporal workflow (business logic)."""
    settings = get_settings()
    client: Client = await get_temporal_client()
    handle = await client.start_workflow(
        CreateShopWorkflow.run,
        CreateShopInput(
            telegram_id=payload.telegram_id,
            name=payload.name,
            description=payload.description,
            username=payload.username,
            first_name=payload.first_name,
        ),
        id=f"create-shop-{payload.telegram_id}-{uuid.uuid4().hex[:8]}",
        task_queue=settings.temporal_task_queue,
    )
    result = await handle.result()
    shop = await db.get(Shop, result.shop_id)
    if shop is None:
        raise HTTPException(status_code=500, detail="Shop created but not found")
    return shop
