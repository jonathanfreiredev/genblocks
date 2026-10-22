from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.settings import settings

# NullPool on purpose: no connection outlives the request that opened it. A platform
# that scales to zero decides from the service's traffic, and a pool holding
# connections open keeps a trickle going that can keep it awake. The API runs one
# worker, so there is no pool worth sharing and little lost by opening a connection
# per request.
engine = create_async_engine(settings.database_url, echo=settings.debug, poolclass=NullPool)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
