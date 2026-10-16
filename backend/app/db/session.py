from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.settings import settings

# NullPool on purpose: no connection outlives the request that opened it. A platform
# that sleeps an idle service decides to do so from that service's traffic, and a
# pool holding connections open keeps a trickle of it going, which is enough to stop
# it ever sleeping. The API serves one instance, so there is no pool to share and
# nothing is lost by opening a connection per request.
engine = create_async_engine(settings.database_url, echo=settings.debug, poolclass=NullPool)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
