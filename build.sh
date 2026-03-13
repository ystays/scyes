#!/bin/bash
set -e

if [ -d ~/Documents/github/scyes ]; then
  cd ~/Documents/github/scyes
else
  cd ~/Documents/scyes
fi

# Start otel-collector if not already running
if ! sudo docker ps --format '{{.Image}}' | grep -q 'opentelemetry-collector-contrib'; then
  echo "Starting otel-collector..."
  sudo docker run -d -p 4318:4318 \
    -v "$(pwd)/observability/otel-collector-config.yaml:/etc/otelcol/config.yaml" \
    --env-file .env \
    otel/opentelemetry-collector-contrib:latest \
    --config /etc/otelcol/config.yaml
else
  echo "otel-collector already running, skipping."
fi

# Check if Ollama is running
curl -s http://localhost:11434 > /dev/null || echo "Warning: Ollama does not appear to be running."

# Stop scyes container if running
if sudo docker ps --format '{{.Image}}' | grep -q 'scyes'; then
  sudo docker stop $(sudo docker ps -q --filter ancestor=scyes)
fi

# Build and run scyes
sudo docker build -t scyes .
sudo docker run -d --network host scyes
