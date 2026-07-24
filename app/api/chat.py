"""Websocket endpoint implementing the chat flow."""

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
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

_client_event_adapter: TypeAdapter[Any] = TypeAdapter(ClientEvent)


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
    async for chunk in agent.stream_reply(session.history()):
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
                    ChatError(message=f"Failed to process event: {exc}").model_dump(mode="json")
                )
    except WebSocketDisconnect:
        # await logger.ainfo("Chat websocket disconnected", session_id=str(session.id))
        pass
    finally:
        await session_manager.remove(session.id)
