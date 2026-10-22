from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Product
from app.schemas.product import ProductFeedItem, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductFeedItem])
async def public_feed(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    shop_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ProductFeedItem]:
    """Public catalog feed — products from all shops (or one shop)."""
    stmt = (
        select(Product)
        .options(selectinload(Product.shop))
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if shop_id is not None:
        stmt = stmt.where(Product.shop_id == shop_id)

    result = await db.execute(stmt)
    products = result.scalars().all()
    return [
        ProductFeedItem(
            id=p.id,
            shop_id=p.shop_id,
            shop_name=p.shop.name if p.shop else "",
            title=p.title,
            description=p.description,
            price=p.price,
            image_url=p.image_url,
            created_at=p.created_at,
        )
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Product not found")
    return product
