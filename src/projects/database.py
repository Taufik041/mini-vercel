from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import SQLModel

_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


def get_engine():
    if _engine is None:
        raise RuntimeError("Engine not initialized")
    return _engine


async def init_db():
    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async_session = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with async_session() as session:
        yield session
