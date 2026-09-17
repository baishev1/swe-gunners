import logging
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import uuid_utils
from sqlalchemy import DateTime, Dialect, Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, declared_attr, mapped_column
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from core.helpers import time_now

__all__ = [
    "UUID",
    "AwareDateTime",
    "DbBase",
    "Session",
    "UTCDateTime",
    "engine",
    "get_db",
    "init_db",
    "uuid7",
]

engine: Engine | None = None

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def uuid7() -> UUID:
    return UUID(str(uuid_utils.uuid7()))


def init_db() -> None:
    from core.settings import settings

    global engine
    logger = logging.getLogger(__name__)

    url = settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    extra_args = {}
    if url.endswith(":memory:"):
        extra_args["poolclass"] = StaticPool
    engine = create_engine(url, echo=settings.DB_ECHO, connect_args=connect_args, **extra_args)

    if url.startswith("sqlite"):
        logger.info("Using SQLite database at %s", settings.SQLITE_FILE_NAME)
    else:
        logger.info(
            "Using PostgreSQL database at %s:%s",
            settings.POSTGRES_SERVER,
            settings.POSTGRES_PORT,
        )


def get_db() -> Iterator[Session]:
    if engine is None:
        raise RuntimeError("Database engine is not initialised, call init_core() first")

    with Session(engine) as session:
        yield session


class UTCDateTime(TypeDecorator[datetime]):
    """
    Forces timezone-aware datetimes for SQLite.
    Saves as naive UTC to the DB, and attaches UTC tzinfo on read.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is not None:
            value = value.replace(tzinfo=UTC)
        return value


AwareDateTime = Annotated[datetime, mapped_column(UTCDateTime)]


class DbBase(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7, sort_order=-100)
    created_at: Mapped[AwareDateTime] = mapped_column(default=time_now, sort_order=100)
    updated_at: Mapped[AwareDateTime] = mapped_column(
        default=time_now, onupdate=time_now, sort_order=100
    )
