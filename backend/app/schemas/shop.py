from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShopCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    telegram_id: int
    username: str | None = None
    first_name: str | None = None


class ShopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None = None
    slug: str
    created_at: datetime
