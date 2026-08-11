[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139.2-009688)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.13.4-e92063)](https://docs.pydantic.dev/)
[![uv](https://img.shields.io/badge/uv-managed-purple)](https://github.com/astral-sh/uv)

# AI Service Backbone

A generic, pluggable AI service built with [FastAPI](https://fastapi.tiangolo.com/). It exposes a streaming WebSocket chat API and a health-check endpoint, with a configurable chat backend that can run as a local stub or connect to any OpenAI-compatible endpoint such as [Ollama](https://ollama.com/).

This repository provides an opinionated starting point for running a stateless, async AI microservice locally or inside Docker.

* * *

## Project Overview

[](#project-overview)

*   **Version:** `0.1.0`
*   **Python:** `>= 3.14`
*   **Key Dependencies:**
    *   `fastapi` (0.139.2)
    *   `pydantic` / `pydantic-settings` (2.13.4 / 2.14.2)
    *   `uvicorn` / `granian` (ASGI servers)
    *   `websockets` (WebSocket client/server support)
    *   `rich` (CLI UX)
    *   `ruff` (linting & formatting)
*   **Infrastructure:** Docker Compose (`compose.yml`)

* * *

## Setup with `uv`

[](#setup-with-uv)

This project uses [`uv`](https://github.com/astral-sh/uv) for fast, reliable Python dependency and environment management.

### 1\. Install `uv`

[](#1-install-uv)

If you don't have `uv` installed, install it via the official installer:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2\. Install Dependencies

[](#2-install-dependencies)

Sync dependencies and set up the local virtual environment:

```bash
uv sync
```

### 3\. Configure the Environment

[](#3-configure-the-environment)

Copy or edit `.env` to choose the chat backend and model endpoint:

```bash
# Example .env
CHAT_BACKEND=ollama
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_MODEL_NAME=llama3.2:1b
OPENAI_API_KEY=optional-api-key
```

*   `CHAT_BACKEND=stub` uses a local echo agent (no network calls, ideal for quick tests).
*   `CHAT_BACKEND=ollama` streams completions from an OpenAI-compatible endpoint.

### 4\. Running Locally with `uv`

[](#4-running-locally-with-uv)

Start the FastAPI application with Granian:

```bash
uv run granian --interface asgi --port 8080 app.main:app --reload
```

The API will be available at `http://localhost:8080`.

* * *

## Running with Docker Compose

[](#running-with-docker-compose)

You can spin up the full service with `docker compose` or `make`:

```bash
# Build images
make docker-build

# Start services
make docker-up
```

Or view available targets:

```bash
make help
```

### Manual `docker compose` commands

[](#manual-docker-compose-commands)

If you prefer to bypass `make`:

```bash
docker compose build
docker compose up --remove-orphans
```

* * *

## Testing the Service

[](#testing-the-service)

Once the API is running, use the interactive WebSocket client to chat with the service.

### Start the chat client

[](#start-the-chat-client)

```bash
python scripts/chit_chat_with_llm.py
```

By default the client connects to `ws://localhost:8080/v1/chat/ws`. You can override the endpoint, system prompt, or connection timeout:

```bash
python scripts/chit_chat_with_llm.py --url ws://localhost:8080/v1/chat/ws --system-prompt "Be concise."
```

### Interactive commands

[](#interactive-commands)

Inside the client you can use:

| Command | Action |
| --- | --- |
| `/start` | Start or restart a conversation. |
| `/history` | Show the full message history. |
| `/end`, `/quit`, `/exit` | Gracefully close the websocket. |
| `/help` | Show the help table. |
| any other text | Send text as a user message. |

### Example session

[](#example-session)

```text
Type /help to see available commands.
You › /start
System prompt (Enter for default) ›
✓ Conversation started. Session ID: <session-id>

You › Hello, what can you do?
Assistant › I am a helpful assistant. How can I help you today?
✓ Message complete (N chunk(s), ... character(s)).

You › /history

You › /end
```

### Health check

[](#health-check)

You can also verify the service is healthy with a simple HTTP request:

```bash
curl http://localhost:8080/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "backend": "ollama",
  "models": ["llama3.2:1b"]
}
```

* * *

## Development

[](#development)

*   **Formatting & Linting:**

    ```bash
    uv run ruff check .
    uv run ruff format .
    ```

*   **Tests:**

    ```bash
    uv run pytest
    ```
