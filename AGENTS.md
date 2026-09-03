# AGENTS.md

This file provides guidance for AI agents working in this repository.

## Project Overview

**scyes** is a self-hosted LLM Discord bot. It supports multiple AI backends (local Ollama models and cloud models via Google Gemini and Grok), an agentic tool-use mode backed by LangChain/LangGraph, a FastAPI HTTP server, OpenTelemetry observability, and an evaluation framework.

## Tech Stack

- **Python 3.13**, dependency manager: `uv`
- **discord.py** — Discord bot framework
- **LangChain / LangGraph** — agent orchestration and tool use
- **Ollama** — local model serving (Gemma 3 family, Mistral, Qwen)
- **Google Gemini / Grok** — cloud model backends
- **FastAPI + uvicorn** — HTTP API server
- **OpenTelemetry + Langfuse** — tracing and LLM observability
- **APScheduler** — in-process task scheduling
- **Ruff** — linting

## How to Run

```bash
# Install dependencies
uv sync

# Run the Discord bot
uv run python -m scyes.bot

# Run the FastAPI server
uv run -m uvicorn scyes.server.server:app --host 0.0.0.0 --port 8000
```

**Docker:**
```bash
./build.sh          # build image and run container
docker-compose up   # bot + OTel collector together
```

## Configuration

All configuration is in `config.ini` (see `config.ini.example` for the template). `config.py` reads every value — use it rather than accessing `config.ini` directly. Required sections:

- `[discord]` — bot token and guild ID
- `[google]` — Gemini API key
- `[tavily]` — search API key
- `[langfuse]` — observability credentials
- `[otel]` — enable/disable OTel, endpoint
- `[homeassistant]` — URL and token for MCP integration

Google Calendar requires `credentials.json` (OAuth2 client) in the repo root; `token.json` is generated on first run.

## Adding a New Tool / Integration

1. Create `src/scyes/integrations/<name>.py` and define a LangChain `Tool` or `@tool`-decorated function.
2. Import and add the tool to the tools list in `src/scyes/llm/agent.py` (inside `invoke_agent` / `astream_agent`).
3. Add any new config values to `config.ini.example` and read them via `config.py`.
4. Add eval cases to `evals/datasets/tool_selection.json` to cover expected tool selection.

## Observability

Every Discord command is traced via OTel. To enable locally:

```bash
docker run --rm -p 4318:4318 \
  -v $(pwd)/src/scyes/observability/otel-collector-config.yaml:/etc/otelcol/config.yaml \
  --env-file .env \
  otel/opentelemetry-collector-contrib:latest
```

Then set `ENABLED = true` under `[otel]` in `config.ini`.

## Async / Threading Pitfalls

### Do not wrap async functions with `asyncio.to_thread`

If a function internally calls `asyncio.run()`, do **not** invoke it via `asyncio.to_thread()`.
`asyncio.to_thread` copies the current context into the thread, but `asyncio.run()` creates a
fresh event loop and a new context. Any `ContextVar` tokens (e.g. OpenTelemetry spans) set inside
`asyncio.run()` will fail to detach, producing:

```
ValueError: <Token ...> was created in a different Context
```

**Wrong:**
```python
# invoke_adk_agent calls asyncio.run() internally
output = await asyncio.to_thread(invoke_adk_agent, message)
```

**Right:** use the async version directly from the async endpoint:
```python
output = await ainvoke_adk_agent(message)
```

Only use `asyncio.to_thread` for blocking synchronous code that has no async counterpart
(e.g. a blocking database driver, CPU-bound work). If the library exposes an async API, use it directly.

## Error Handling

### Use `logger.exception` instead of `traceback.print_exc`

Prefer `logger.exception(...)` over `traceback.print_exc()` in exception handlers. `logger.exception` logs the message and full traceback through the standard logging system (respecting log level, handlers, and formatters), whereas `traceback.print_exc()` writes directly to stderr and bypasses logging entirely.

**Wrong:**
```python
except Exception as e:
    traceback.print_exc()
    yield AIMessageChunk(content=f"Error: {str(e)}")
```

**Right:**
```python
except Exception as e:
    logger.exception("Descriptive error message")
    yield AIMessageChunk(content=f"Error: {str(e)}")
```

When using `logger.exception`, there is no need to import `traceback`.

## Key Conventions

- All LLM calls go through `llm/agent.py` (agent) or `llm/llm.py` (simple streaming) — do not call Ollama or Google SDKs directly elsewhere.
- Async throughout: Discord commands use `async def`, agent functions use `astream_agent` for streaming and `invoke_agent` for single-turn HTTP calls.
- Linting: `ruff check .` — keep code clean before committing.
- Secrets never committed: `.env` and `config.ini` are gitignored; use `config.ini.example` for templates.
