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
    -v "$(pwd)/src/scyes/observability/otel-collector-config.yaml:/etc/otelcol/config.yaml" \
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
build_log=$(mktemp)
if ! sudo docker build -t scyes . 2>&1 | tee "$build_log"; then
  if grep -qi "no space left on device\|out of disk space\|no space left" "$build_log"; then
    echo "Error: Docker build failed — disk is full. Free up space and try again."
    df -h /
  else
    echo "Error: Docker build failed."
  fi
  rm -f "$build_log"
  exit 1
fi
rm -f "$build_log"
sudo docker run -d --network host scyes
