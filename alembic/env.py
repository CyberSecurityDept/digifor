from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.db.base import Base
from app.suspect_management.models import Suspect
from app.case_management.models import Case, CaseLog, Agency
from app.evidence_management.models import Evidence, CustodyLog
from app.auth.models import User
from app.analytics.analytics_management.models import Analytic
from app.analytics.device_management.models import File

try:
    from app.analytics.device_management.models import Device, HashFile, Contact, Call, SocialMedia, ChatMessage
except ImportError:
    pass

target_metadata = Base.metadata

def get_url():
    from app.core.config import settings
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

