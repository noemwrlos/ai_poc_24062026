import os
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatConfig(BaseModel):
    """Configuration for the websocket chat service's model-client adapter.

    ``backend`` selects which :class:`~app.services.chat_agent.ChatAgent`
    implementation is built by
    :func:`~app.services.chat_agent.build_chat_agent` during app startup:

    - ``"stub"``: a local, dependency-free echo agent (default, no network
      calls, ideal for local dev/tests).
    - ``"ollama"``: streams completions from an OpenAI-compatible endpoint
      (e.g. a local Ollama server), reusing the same adapter interface.
    """

    backend: Literal["stub", "ollama"] = os.getenv("CHAT_BACKEND", "ollama")
    base_url: str = os.getenv("CHAT_BASE_URL", "http://localhost:11434/v1")
    model: str = os.getenv("CHAT_MODEL", "llama3.2:1b")
    stream_delay_seconds: float = float(os.getenv("CHAT_STREAM_DELAY", "0.02"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    chat: ChatConfig = ChatConfig()

settings = Settings()