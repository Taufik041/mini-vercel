import os
import sys
import uuid
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# At the top of tests/projects/conftest.py, before imports
# Remove any previously imported 'main' to avoid auth's main bleeding in
for mod in list(sys.modules.keys()):
    if mod in ("main", "database", "models", "endpoints"):
        del sys.modules[mod]


_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_here, "../../src/projects")))
sys.path.insert(0, os.path.abspath(os.path.join(_here, "../../src")))

from database import set_engine  # noqa: E402 #type: ignore
from main import app  # noqa: E402 #type: ignore

from common.utils import create_access_token  # noqa: E402

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
def auth_headers():
    token = create_access_token({"sub": str(uuid.uuid4())}, timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(test_engine):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def existing_project(client, auth_headers):
    response = await client.post(
        "/projects",
        json={
            "name": "existing-app",
            "git_url": "https://github.com/test/repo",
            "port": 3000,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    return response.json()
