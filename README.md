# scyes

A locally-hosted LLM Discord bot

## uv
https://docs.astral.sh/uv/getting-started/installation/#installation-methods

```
uv run api_server.py
uv run bot.py
```

## ngrok
Ngrok is only needed for Discord interactions
```
ngrok http --domain=evidently-loyal-trout.ngrok-free.app 8000
```

https://ngrok.com/docs/agent#try-it-out
https://ngrok.com/docs/agent/config
```

ngrok service install --config C:\ngrok\ngrok.yml
ngrok service start
```

## discord
Interactions endpoint: https://evidently-loyal-trout.ngrok-free.app/interactions

## docker
```
# Build Docker image
sudo docker build -t scyes .

# Run Docker container (detach, with host network)
sudo docker run -d --network host scyes:0.0.1

# docker-compose
docker-compose exec ollama ollama pull <model_name>
```



## OpenTelemetry collector
Run a local collector that receives OTLP HTTP traces and logs them to stdout:

```bash
docker run --rm -p 4318:4318 \
  -v $(pwd)/observability/otel-collector-config.yaml:/etc/otelcol/config.yaml \
  otel/opentelemetry-collector:latest
```

Then enable telemetry in `config.ini`:

```ini
[otel]
ENABLED = true
SERVICE_NAME = scyes
OTLP_HTTP_ENDPOINT = http://localhost:4318/v1/traces
```

With this enabled, each Discord bot command call creates a `discord.command` span with command, user, channel, and guild attributes.

## MCP
Home Assistant: https://www.home-assistant.io/integrations/mcp_server/