from aiogram import Router

from bot.handlers.catalog import router as catalog_router
from bot.handlers.products import router as products_router
from bot.handlers.shops import router as shops_router
from bot.handlers.start import router as start_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(start_router)
    root.include_router(shops_router)
    root.include_router(products_router)
    root.include_router(catalog_router)
    return root
