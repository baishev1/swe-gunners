"""
Startup and shutdown events for fast api app
"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager, run_in_threadpool

import core

logger = logging.getLogger(__name__)


def _expire_stale_orders() -> int:
    from features.orders.service import order_service

    if core.engine is None:
        return 0
    with core.Session(core.engine) as db:
        return order_service.expire_stale_orders(db)


async def _sweep_expired_holds(interval: int) -> None:
    """Periodically releases inventory held by abandoned checkouts (SRS 4.3, 4.6).

    Checkout also sweeps on demand, so this loop only keeps the counters honest
    while nobody is buying.
    """
    while True:
        await asyncio.sleep(interval)
        try:
            expired = await run_in_threadpool(_expire_stale_orders)
            if expired:
                logger.info("Released %d expired checkout hold(s)", expired)
        except Exception:
            logger.exception("Expired checkout sweep failed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    core.init_core()

    sweeper: asyncio.Task[None] | None = None
    interval = core.settings.ORDER_SWEEP_INTERVAL_SECONDS
    if interval > 0:
        sweeper = asyncio.create_task(_sweep_expired_holds(interval))

    yield

    if sweeper is not None:
        sweeper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sweeper
    if core.engine is not None:
        core.engine.dispose()
