import importlib
import logging
import pkgutil
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context
from core.database import DbBase, UTCDateTime
from core.settings import settings

config = context.config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

config.set_main_option("sqlalchemy.url", settings.database_url)

# Import every features/<name>/models.py so autogenerate sees the full metadata.
features_path = PROJECT_ROOT / "features"
if features_path.exists():
    for module_info in pkgutil.iter_modules([str(features_path)]):
        try:
            importlib.import_module(f"features.{module_info.name}.models")
            logger.info("Alembic auto-imported: features.%s.models", module_info.name)
        except ModuleNotFoundError:
            pass

target_metadata = DbBase.metadata


def render_item(type_, obj, autogen_context):
    """Keep migrations free of app imports: UTCDateTime stores as a plain DateTime."""
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime()"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
