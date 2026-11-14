from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import get_settings

engine = create_async_engine(get_settings().database_url.get_secret_value(), pool_pre_ping=True, hide_parameters=True)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with Session() as session:
        async with session.begin():
            yield session
