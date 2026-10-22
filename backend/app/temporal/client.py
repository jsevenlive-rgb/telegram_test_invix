from functools import lru_cache

from temporalio.client import Client

from app.config import get_settings


@lru_cache
def _client_holder() -> dict:
    return {"client": None}


async def get_temporal_client() -> Client:
    holder = _client_holder()
    if holder["client"] is None:
        settings = get_settings()
        holder["client"] = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
    return holder["client"]
