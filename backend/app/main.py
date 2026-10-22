from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.media import router as media_router
from app.api.products import router as products_router
from app.api.shops import router as shops_router
from app.config import get_settings
from app.database import init_db
from app.services.s3 import ensure_bucket


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    try:
        ensure_bucket()
    except Exception as exc:  # MinIO may start a bit later
        print(f"MinIO bucket init deferred: {exc}")
    yield


settings = get_settings()

app = FastAPI(
    title="Shop Bot API",
    description="Public product feed + shops for Telegram Mini App",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router, prefix="/api")
app.include_router(shops_router, prefix="/api")
app.include_router(media_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
