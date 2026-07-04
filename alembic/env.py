from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

# Import application settings and models for autogenerate mapping
from app.config.config import settings
from app.database.session import Base
# Import all model entities so metadata registration is complete
from app.models.models import User, Organization, Invitation, AuditLog

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata maps SQLAlchemy ORM Base metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use dynamic settings URL instead of hardcoded config file URL
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Force SQLite for development to avoid PostgreSQL connection issues
    database_url = "sqlite:///./focusguard.db"
    
    # Create engine directly from settings.DATABASE_URL
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True  # Enables batch migrations for SQLite compatibility
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

