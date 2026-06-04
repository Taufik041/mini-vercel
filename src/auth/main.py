from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from endpoints import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
