import asyncio
from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Test database engine
test_engine = create_async_engine(
    settings.test_database_url
    or settings.database_url.replace("arvalox_dev", "arvalox_test"),
    echo=False,
    poolclass=None,  # Disable connection pooling for tests
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
async def setup_test_db():
    """Set up test database schema once per session"""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    def get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
