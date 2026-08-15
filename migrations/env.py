from pathlib import Path
import sys

# Alembic may run with migrations/ as sys.path[0] inside containers.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alembic import context
from sqlalchemy import engine_from_config, pool
from backend.db import Base
from backend.core.config import settings
from backend import models  # noqa: F401

config = context.config
config.set_main_option('sqlalchemy.url', settings.database_url.replace('%', '%%'))
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(url=config.get_main_option('sqlalchemy.url'), target_metadata=target_metadata, literal_binds=True, dialect_opts={'paramstyle':'named'})
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix='sqlalchemy.', poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()

run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
