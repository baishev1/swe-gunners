from fastapi import HTTPException  # noqa: F401

from .database import *
from .helpers import *
from .settings import *


def init_core() -> None:
    # init logging first
    from .logging import init_logging

    init_logging()

    # init everything else
    from .database import init_db

    init_db()
