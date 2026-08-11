from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.chat import router as chat_ws_router
from app.api.health import router as health_router
from app.config import settings as global_settings
from app.services.chat_agent import build_chat_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.chat_agent = build_chat_agent(global_settings.chat)
    try:
        yield
    except Exception:
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
    app.include_router(health_router, prefix="/v1", tags=["Health"])
    return app


app = create_app()
