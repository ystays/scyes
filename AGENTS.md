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
uv run bot.py

# Run the FastAPI server
uv run -m uvicorn server.server:app --host 0.0.0.0 --port 8000
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

1. Create `integrations/<name>.py` and define a LangChain `Tool` or `@tool`-decorated function.
2. Import and add the tool to the tools list in `llm/agent.py` (inside `invoke_agent` / `astream_agent`).
3. Add any new config values to `config.ini.example` and read them via `config.py`.
4. Add eval cases to `evals/datasets/tool_selection.json` to cover expected tool selection.

## Observability

Every Discord command is traced via OTel. To enable locally:

```bash
docker run --rm -p 4318:4318 \
  -v $(pwd)/observability/otel-collector-config.yaml:/etc/otelcol/config.yaml \
  --env-file .env \
  otel/opentelemetry-collector-contrib:latest
```

Then set `ENABLED = true` under `[otel]` in `config.ini`.

## Key Conventions

- All LLM calls go through `llm/agent.py` (agent) or `llm/llm.py` (simple streaming) — do not call Ollama or Google SDKs directly elsewhere.
- Async throughout: Discord commands use `async def`, agent functions use `astream_agent` for streaming and `invoke_agent` for single-turn HTTP calls.
- Linting: `ruff check .` — keep code clean before committing.
- Secrets never committed: `.env` and `config.ini` are gitignored; use `config.ini.example` for templates.
