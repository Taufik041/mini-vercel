import os
from uuid import UUID

from schemas import User
from security import hash_password
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

_engine = None
_factory = None


def set_engine(new_engine):
    global _engine, _factory
    _engine = new_engine
    _factory = (
        async_sessionmaker(new_engine, expire_on_commit=False) if new_engine else None
    )


def _get_factory():
    global _engine, _factory
    if _engine is None:
        _engine = create_async_engine(os.environ.get("DATABASE_URL", ""), echo=True)
        _factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _factory


async def get_session():
    async with _get_factory()() as session:
        yield session


async def init_db():
    _get_factory()
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with _factory() as session:
        admin = (
            (
                await session.execute(
                    select(User).where(User.email == os.environ.get("ADMIN_EMAIL", ""))
                )
            )
            .scalars()
            .first()
        )
        if not admin:
            session.add(
                User(
                    id=UUID(os.environ.get("ADMIN_ID")),
                    name=os.environ.get("ADMIN_NAME", ""),
                    email=os.environ.get("ADMIN_EMAIL", ""),
                    creds=float(os.environ.get("ADMIN_CREDS", 0.0)),
                    password=hash_password(os.environ.get("ADMIN_PASSWORD", "")),
                    is_active=True,
                )
            )
            await session.commit()
