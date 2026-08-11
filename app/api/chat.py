"""Websocket endpoint implementing the chat flow."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from pydantic import TypeAdapter, ValidationError

from app.schemas.chat import (
    AssistantChunk,
    AssistantMessage,
    ChatError,
    ChatMessage,
    ClientEvent,
    Connected,
    ConversationStarted,
    EndConversation,
    HistoryResponse,
    RequestHistory,
    SendUserMessage,
    StartConversation,
)
from app.services.chat_agent import ChatAgent
from app.services.chat_session import ChatSession, ChatSessionManager

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_client_event_adapter: TypeAdapter[Any] = TypeAdapter(ClientEvent)


def _websocket_url_for_request(request: Request) -> str:
    """Build the websocket URL that matches the current HTTP request."""
    ws_scheme = "wss" if request.url.scheme == "https" else "ws"
    ws_path = request.url_for("chat_websocket").path
    return f"{ws_scheme}://{request.url.netloc}{ws_path}"


async def _batched_chunks(
    source: AsyncIterator[str],
    max_interval: float = 0.05,
    max_chars: int = 128,
) -> AsyncIterator[str]:
    """Buffer small streamed chunks and flush them in fewer frames.

    Tiny model tokens arrive very quickly; sending each one as a separate
    WebSocket message and re-rendering the UI per token is expensive. This
    generator batches them by time (``max_interval``) or by accumulated size
    (``max_chars``), whichever comes first, while still preserving the same
    wire format (each yielded item is sent as one ``assistant_chunk``).
    """
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def pump() -> None:
        async for chunk in source:
            await queue.put(chunk)
        await queue.put(None)

    pump_task = asyncio.create_task(pump())
    buffer: list[str] = []
    buffered_chars = 0

    try:
        while True:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=max_interval)
            except TimeoutError:
                if buffer:
                    yield "".join(buffer)
                    buffer.clear()
                    buffered_chars = 0
                continue

            if chunk is None:
                if buffer:
                    yield "".join(buffer)
                break

            buffer.append(chunk)
            buffered_chars += len(chunk)

            if buffered_chars >= max_chars:
                yield "".join(buffer)
                buffer.clear()
                buffered_chars = 0
    finally:
        pump_task.cancel()
        try:
            await pump_task
        except asyncio.CancelledError:
            pass


async def _handle_start(
    websocket: WebSocket, session: ChatSession, event: StartConversation
) -> None:
    session.messages.clear()
    if event.system_prompt:
        session.add(ChatMessage(role="system", content=event.system_prompt))
    await websocket.send_json(
        ConversationStarted(session_id=session.id).model_dump(mode="json")
    )


async def _handle_user_message(
    websocket: WebSocket, session: ChatSession, agent: ChatAgent, event: SendUserMessage
) -> None:
    session.add(ChatMessage(role="user", content=event.content))

    chunks: list[str] = []
    index = 0
    async for chunk in _batched_chunks(agent.stream_reply(session.history())):
        chunks.append(chunk)
        await websocket.send_json(
            AssistantChunk(index=index, content=chunk).model_dump(mode="json")
        )
        index += 1

    assistant_message = ChatMessage(role="assistant", content="".join(chunks))
    session.add(assistant_message)
    await websocket.send_json(
        AssistantMessage(message=assistant_message).model_dump(mode="json")
    )


async def _handle_history_request(websocket: WebSocket, session: ChatSession) -> None:
    await websocket.send_json(
        HistoryResponse(messages=session.history()).model_dump(mode="json")
    )


@router.get("/", include_in_schema=False)
async def chat_page(request: Request) -> Any:
    """Serve the web chat client."""
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"ws_url": _websocket_url_for_request(request)},
    )


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket) -> None:
    """Websocket chat endpoint. See module docstring for the event flow."""
    await websocket.accept()

    agent: ChatAgent = websocket.app.chat_agent
    session_manager: ChatSessionManager = ChatSessionManager()
    session = await session_manager.create()

    await websocket.send_json(Connected(session_id=session.id).model_dump(mode="json"))

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                event = _client_event_adapter.validate_python(raw)
            except ValidationError as exc:
                await websocket.send_json(
                    ChatError(message=f"Invalid event: {exc}").model_dump(mode="json")
                )
                continue

            try:
                match event:
                    case StartConversation():
                        await _handle_start(websocket, session, event)
                    case SendUserMessage():
                        await _handle_user_message(websocket, session, agent, event)
                    case RequestHistory():
                        await _handle_history_request(websocket, session)
                    case EndConversation():
                        break
            except Exception as exc:  # noqa: BLE001
                await websocket.send_json(
                    ChatError(message=f"Failed to process event: {exc}").model_dump(
                        mode="json"
                    )
                )
    except WebSocketDisconnect:
        # await logger.ainfo("Chat websocket disconnected", session_id=str(session.id))
        pass
    finally:
        await session_manager.remove(session.id)
