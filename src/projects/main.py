import os
from contextlib import asynccontextmanager

from database import init_db, set_engine
from endpoints import router
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=True)
    set_engine(engine)
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
