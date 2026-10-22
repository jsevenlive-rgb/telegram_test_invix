import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.config import get_settings
from app.temporal.activities import (
    ensure_user_and_create_shop,
    fetch_and_store_product_image,
    get_user_shops,
    save_product,
)
from app.temporal.workflows import CreateProductWorkflow, CreateShopWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[CreateShopWorkflow, CreateProductWorkflow],
        activities=[
            ensure_user_and_create_shop,
            fetch_and_store_product_image,
            save_product,
            get_user_shops,
        ],
    )
    logger.info(
        "Temporal worker started on queue=%s host=%s",
        settings.temporal_task_queue,
        settings.temporal_host,
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
