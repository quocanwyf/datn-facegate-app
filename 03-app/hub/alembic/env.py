from alembic import context
from sqlalchemy import create_engine
from app.config import get_settings
from app.db.models import Base

config = context.config
url = get_settings().database_url.get_secret_value().replace('postgresql+asyncpg:', 'postgresql+psycopg:')


def run_migrations_online():
    engine = create_engine(url, hide_parameters=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
