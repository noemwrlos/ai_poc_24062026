"""Pydantic models for the websocket chat service."""

from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    """A single role-labeled message, matching Pydantic AI message shapes."""

    role: Role
    content: str


# --------------------------------------------------------------------------
# Client -> Server events
# --------------------------------------------------------------------------


class StartConversation(BaseModel):
    """Sent by the client to (re)start a conversation, optionally seeding it
    with a system prompt."""

    type: Literal["start"] = "start"
    system_prompt: str | None = None


class SendUserMessage(BaseModel):
    """Sent by the client with a new user message to append to history and
    forward to the agent."""

    type: Literal["user_message"] = "user_message"
    content: str


class RequestHistory(BaseModel):
    """Sent by the client to request the full message history for the
    current session."""

    type: Literal["history_request"] = "history_request"


class EndConversation(BaseModel):
    """Sent by the client to gracefully close the conversation/websocket."""

    type: Literal["end"] = "end"


ClientEvent = Annotated[
    StartConversation | SendUserMessage | RequestHistory | EndConversation,
    Field(discriminator="type"),
]


# --------------------------------------------------------------------------
# Server -> Client events
# --------------------------------------------------------------------------


class Connected(BaseModel):
    """First event sent right after the websocket handshake completes."""

    type: Literal["connected"] = "connected"
    session_id: UUID = Field(default_factory=uuid4)


class ConversationStarted(BaseModel):
    """Acknowledges a ``start`` event."""

    type: Literal["started"] = "started"
    session_id: UUID


class AssistantChunk(BaseModel):
    """A single streamed token/chunk of the assistant's reply."""

    type: Literal["assistant_chunk"] = "assistant_chunk"
    index: int
    content: str


class AssistantMessage(BaseModel):
    """The final, aggregated assistant message once streaming completes."""

    type: Literal["assistant_message"] = "assistant_message"
    message: ChatMessage


class HistoryResponse(BaseModel):
    """Response to a ``history_request`` event."""

    type: Literal["history"] = "history"
    messages: list[ChatMessage]


class ChatError(BaseModel):
    """Emitted whenever something goes wrong processing a client event."""

    type: Literal["error"] = "error"
    message: str


ServerEvent = (
    Connected
    | ConversationStarted
    | AssistantChunk
    | AssistantMessage
    | HistoryResponse
    | ChatError
)