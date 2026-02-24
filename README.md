# scyes

A self-hosted LLM Discord bot. 

Featuring Ollama, OTel with Grafana, Google AI Studio and Gemini, Home Assistant, and Tavily Search.

## uv
https://docs.astral.sh/uv/getting-started/installation/#installation-methods

```
uv run api_server.py
uv run bot.py
```

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
sudo docker run --rm -p 4318:4318 \
  -v $(pwd)/observability/otel-collector-config.yaml:/etc/otelcol/config.yaml \
  --env-file .env \
  otel/opentelemetry-collector-contrib:latest \
  --config /etc/otelcol/config.yaml
```

Then enable telemetry in `config.ini`:

```ini
[otel]
ENABLED = true
SERVICE_NAME = scyes
OTLP_HTTP_ENDPOINT = http://localhost:4318
```

With this enabled, each Discord bot command call creates a `discord.command` span with command, user, channel, and guild attributes.

Check out this video/article on using the OTel Collector with Loki: https://grafana.com/docs/grafana-cloud/send-data/logs/collect-logs-with-otel/

Collector config documentation: https://opentelemetry.io/docs/collector/configuration/

## Integrations and MCP
Home Assistant: https://www.home-assistant.io/integrations/mcp_server/

---

## Other: Discord Interactions

### ngrok
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

### discord
Interactions endpoint: https://evidently-loyal-trout.ngrok-free.app/interactions
