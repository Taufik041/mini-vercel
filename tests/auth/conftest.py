from main import app  # type: ignore
from database import set_engine  # type: ignore
from schemas import User  # type: ignore
from security import hash as hash_password  # type: ignore
from common.utils import create_access_token

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("ADMIN_ID", "00000000-0000-0000-0000-000000000001")
os.environ.setdefault("ADMIN_NAME", "Admin")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_CREDS", "100.0")
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass123!")


import pytest
from uuid import uuid4
from datetime import timedelta
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_here, "../../src/auth")))
sys.path.insert(0, os.path.abspath(os.path.join(_here, "../../src")))

_SQLITE_URL = "sqlite+aiosqlite://"
_TEST_USER_EMAIL = "testuser@example.com"
_TEST_USER_PASSWORD = "correctpassword"


@pytest.fixture(autouse=True)
async def test_engine():
    engine = create_async_engine(
        _SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    set_engine(engine)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()
    set_engine(None)


@pytest.fixture
async def client(test_engine):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def existing_user(test_engine):
    async with AsyncSession(test_engine) as session:
        user = User(
            id=uuid4(),
            name="Test User",
            email=_TEST_USER_EMAIL,
            creds=10.0,
            password=hash_password(_TEST_USER_PASSWORD),
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def valid_token(existing_user):
    return create_access_token(
        data={"user_id": str(existing_user.id)},
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
async def authenticated_client(client, valid_token):
    client.headers.update({"Authorization": f"Bearer {valid_token}"})
    yield client
