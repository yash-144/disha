from typing import AsyncGenerator
from app.core.config import settings

try:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.orm import DeclarativeBase

    _url = settings.DISHA_DATABASE_URL
    _kwargs = {}
    if "supabase" in _url:
        # Supabase needs TLS, and its pgbouncer pooler cannot use asyncpg's prepared-statement cache.
        _kwargs["connect_args"] = {"ssl": "require", "statement_cache_size": 0}
        _kwargs["pool_pre_ping"] = True
        _kwargs["pool_size"] = 5
        _kwargs["max_overflow"] = 5

    engine = create_async_engine(
        _url,
        echo=False,
        future=True,
        **_kwargs,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    class Base(DeclarativeBase):
        pass

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

except ImportError:
    # Graceful fallback when sqlalchemy is not yet installed in local environment
    class Base:
        __tablename__ = ""
        metadata = None

    AsyncSession = object
    engine = None
    AsyncSessionLocal = None

    async def get_db():
        yield None
