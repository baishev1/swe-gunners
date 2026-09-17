from fastapi import HTTPException  # noqa: F401

from .database import *
from .helpers import *
from .settings import *


def init_core() -> None:
    from .logging import init_logging

    init_logging()

    from .database import init_db

    init_db()

    from . import database

    globals()["engine"] = database.engine


def __getattr__(name: str):
    if name == "engine":
        from . import database

        return database.engine
    raise AttributeError(f"module 'core' has no attribute '{name}'")
