import asyncio
import logging
import os
import socket
from datetime import timedelta

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    Interceptor,
    Worker,
)

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


def build_worker_identity(prefix: str = "") -> str:
    """Unique per process. Shared .env must not collapse replicas onto one identity."""
    host = os.environ.get("HOSTNAME") or socket.gethostname()
    unique = f"{host}:{os.getpid()}"
    label = prefix.strip()
    return f"{label}:{unique}" if label else unique


class _ActivityIdentityInterceptor(Interceptor):
    def __init__(self, identity: str) -> None:
        self._identity = identity

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        return _ActivityIdentityInbound(next, self._identity)


class _ActivityIdentityInbound(ActivityInboundInterceptor):
    def __init__(self, next: ActivityInboundInterceptor, identity: str) -> None:
        super().__init__(next)
        self._identity = identity

    async def execute_activity(self, input: ExecuteActivityInput) -> object:
        info = activity.info()
        logger.info(
            "activity start identity=%s type=%s activity_id=%s workflow_id=%s attempt=%s",
            self._identity,
            info.activity_type,
            info.activity_id,
            info.workflow_id,
            info.attempt,
        )
        try:
            result = await self.next.execute_activity(input)
        except Exception:
            logger.exception(
                "activity failed identity=%s type=%s workflow_id=%s attempt=%s",
                self._identity,
                info.activity_type,
                info.workflow_id,
                info.attempt,
            )
            raise
        logger.info(
            "activity done identity=%s type=%s workflow_id=%s attempt=%s",
            self._identity,
            info.activity_type,
            info.workflow_id,
            info.attempt,
        )
        return result


async def main() -> None:
    settings = get_settings()
    identity = build_worker_identity(settings.worker_identity)
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        identity=identity,
        workflows=[CreateShopWorkflow, CreateProductWorkflow],
        activities=[
            ensure_user_and_create_shop,
            fetch_and_store_product_image,
            save_product,
            get_user_shops,
        ],
        interceptors=[_ActivityIdentityInterceptor(identity)],
        # On SIGTERM, finish in-flight work briefly, then cancel the rest so
        # another replica polling the same queue can retry them.
        graceful_shutdown_timeout=timedelta(seconds=25),
    )
    logger.info(
        "Temporal worker started identity=%s queue=%s host=%s",
        identity,
        settings.temporal_task_queue,
        settings.temporal_host,
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
