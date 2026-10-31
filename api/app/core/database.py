from typing import AsyncGenerator
from app.core.config import settings

try:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.orm import DeclarativeBase

    engine = create_async_engine(
        settings.DISHA_DATABASE_URL,
        echo=(settings.DISHA_ENV == "development"),
        future=True
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
