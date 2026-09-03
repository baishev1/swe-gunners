"""
Startup and shutdown events for fast api app
"""

from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

import core


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    core.init_core()

    yield

    if core.engine is not None:
        core.engine.dispose()
