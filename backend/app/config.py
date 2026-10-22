from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = ""
    admin_ids: str = ""
    # socks5h://user:pass@host:port — needed when VPS cannot reach api.telegram.org
    telegram_proxy_url: str = ""
    webapp_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    database_url: str = "postgresql+asyncpg://shop:shop_secret@localhost:5432/shop_db"

    # local | s3. Production uses MinIO (s3).
    storage_backend: str = "s3"
    media_root: str = "/data/media"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "products"
    minio_secure: bool = False
    minio_public_url: str = "http://localhost:9000"

    api_cors_origins: str = "http://localhost:3000,https://web.telegram.org"

    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "shop-bot-queue"
    # Optional label. Hostname and pid are always appended so replicas stay unique.
    worker_identity: str = ""

    @property
    def admin_id_list(self) -> list[int]:
        if not self.admin_ids.strip():
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_id_list


@lru_cache
def get_settings() -> Settings:
    return Settings()
