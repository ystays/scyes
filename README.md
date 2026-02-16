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


## MCP
Home Assistant: https://www.home-assistant.io/integrations/mcp_server/