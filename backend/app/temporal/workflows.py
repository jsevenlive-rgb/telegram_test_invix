from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.temporal.activities import (
        ensure_user_and_create_shop,
        fetch_and_store_product_image,
        save_product,
    )
    from app.temporal.shared import (
        CreateProductInput,
        CreateProductResult,
        CreateShopInput,
        CreateShopResult,
        ProductRecord,
    )


_retry = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=5,
)


@workflow.defn
class CreateShopWorkflow:
    """Business logic: register user (if needed) and create a storefront."""

    @workflow.run
    async def run(self, data: CreateShopInput) -> CreateShopResult:
        return await workflow.execute_activity(
            ensure_user_and_create_shop,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=_retry,
        )


@workflow.defn
class CreateProductWorkflow:
    """
    Business logic for placing a product on a shop showcase:
    1) download photo from Telegram + upload to MinIO S3
    2) persist product row in PostgreSQL
    """

    @workflow.run
    async def run(self, data: CreateProductInput) -> CreateProductResult:
        image_key, image_url = await workflow.execute_activity(
            fetch_and_store_product_image,
            data,
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=_retry,
        )

        record = ProductRecord(
            shop_id=data.shop_id,
            title=data.title,
            description=data.description,
            price=data.price,
            image_key=image_key,
            image_url=image_url,
        )

        return await workflow.execute_activity(
            save_product,
            record,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=_retry,
        )
