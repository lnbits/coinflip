import asyncio

from fastapi import APIRouter
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import coinflip_generic_router
from .views_api import coinflip_api_router

coinflip_ext: APIRouter = APIRouter(prefix="/coinflip", tags=["coinflip"])
coinflip_ext.include_router(coinflip_generic_router)
coinflip_ext.include_router(coinflip_api_router)
coinflip_ext.include_router(coinflip_lnurl_router)

coinflip_static_files = [
    {
        "path": "/coinflip/static",
        "name": "coinflip_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def coinflip_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def coinflip_start():
    task = create_permanent_unique_task("ext_coinflip", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = ["db", "coinflip_ext", "coinflip_static_files"]
