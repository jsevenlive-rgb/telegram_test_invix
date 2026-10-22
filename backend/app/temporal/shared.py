from dataclasses import dataclass


@dataclass
class CreateShopInput:
    telegram_id: int
    name: str
    description: str | None = None
    username: str | None = None
    first_name: str | None = None


@dataclass
class CreateShopResult:
    shop_id: int
    slug: str
    name: str


@dataclass
class CreateProductInput:
    shop_id: int
    title: str
    telegram_file_id: str
    description: str | None = None
    price: str | None = None


@dataclass
class CreateProductResult:
    product_id: int
    title: str
    image_url: str
    shop_id: int


@dataclass
class ProductRecord:
    shop_id: int
    title: str
    description: str | None
    price: str | None
    image_key: str
    image_url: str
