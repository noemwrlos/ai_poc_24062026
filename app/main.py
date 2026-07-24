from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request

from app.api.chat import router as chat_ws_router

from app.config import settings as global_settings
from app.services.chat_agent import build_chat_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.chat_agent = build_chat_agent(global_settings.chat)
    try:
        yield
    except Exception as e:
        raise
    finally:
        await app.chat_agent.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AKMF AI Generic Service",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(chat_ws_router, prefix="/v1/chat", tags=["Chat"])
    return app

app = create_app()
