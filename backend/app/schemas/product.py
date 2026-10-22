from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shop_id: int
    title: str
    description: str | None = None
    price: Decimal | None = None
    image_key: str
    image_url: str
    created_at: datetime


class ProductFeedItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shop_id: int
    shop_name: str
    title: str
    description: str | None = None
    price: Decimal | None = None
    image_url: str
    created_at: datetime
