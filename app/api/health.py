"""HTTP healthcheck endpoint for the chat service."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.chat_agent import ChatAgent

router = APIRouter()


class HealthResponse(BaseModel):
    """Healthcheck response exposing backend status and available models."""

    status: str
    backend: str
    models: list[str]


@router.get("/health", response_model=HealthResponse)
async def healthcheck(request: Request) -> HealthResponse:
    """Return service health and the list of models from the configured backend.

    The model list is fetched through the active :class:`ChatAgent`
    (``OllamaChatAgent`` when ``CHAT_BACKEND=ollama``), so it validates that
    the OpenAI-compatible endpoint is reachable and honours the ``OPENAI_*``
    configuration loaded from ``.env``.
    """
    agent: ChatAgent = request.app.chat_agent
    models = await agent.list_models()
    backend = "ollama" if agent.__class__.__name__ == "OllamaChatAgent" else "stub"
    return HealthResponse(status="ok", backend=backend, models=models)
