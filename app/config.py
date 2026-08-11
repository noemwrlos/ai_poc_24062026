from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatConfig(BaseSettings):
    """Configuration for the websocket chat service's model-client adapter.

    Values are read from the ``.env`` file (or environment variables). The
    OpenAI-compatible endpoint settings use ``OPENAI_*`` variable names so
    the same configuration works for Ollama, OpenAI, or any compatible
    provider.

    ``backend`` selects which :class:`~app.services.chat_agent.ChatAgent`
    implementation is built by
    :func:`~app.services.chat_agent.build_chat_agent` during app startup:

    - ``"stub"``: a local, dependency-free echo agent (default, no network
      calls, ideal for local dev/tests).
    - ``"ollama"``: streams completions from an OpenAI-compatible endpoint
      (e.g. a local Ollama server), reusing the same adapter interface.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        populate_by_name=True,
    )

    backend: Literal["stub", "ollama"] = Field(
        default="ollama", alias="CHAT_BACKEND"
    )
    base_url: str = Field(
        default="http://localhost:11434/v1", alias="OPENAI_API_BASE"
    )
    model: str = Field(default="llama3.2:1b", alias="OPENAI_MODEL_NAME")
    api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    stream_delay_seconds: float = Field(default=0.02, alias="CHAT_STREAM_DELAY")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        env_nested_class_seperator="__",
    )

    chat: ChatConfig = Field(default_factory=ChatConfig)


settings = Settings()
