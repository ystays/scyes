import json
import logging
import time
import base64
from datetime import UTC, datetime
from urllib import request

from config import app_config


class GrafanaLokiHandler(logging.Handler):
    def __init__(self, endpoint: str, username: str, password: str, labels: dict[str, str]):
        super().__init__()
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.labels = labels

    def emit(self, record: logging.LogRecord) -> None:
        timestamp_ns = str(int(time.time() * 1_000_000_000))
        payload = {
            "streams": [
                {
                    "stream": self.labels,
                    "values": [[timestamp_ns, self.format(record)]],
                }
            ]
        }

        req = request.Request(
            url=self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        req.add_header(
            "Authorization",
            "Basic "
            + base64.b64encode(
                f"{self.username}:{self.password}".encode("utf-8")
            ).decode("ascii"),
        )

        try:
            with request.urlopen(req, timeout=5):
                pass
        except Exception:
            # Don't crash the bot on logging transport failures.
            self.handleError(record)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        optional_fields = [
            "event",
            "command",
            "guild_id",
            "channel_id",
            "user_id",
            "latency_ms",
        ]
        for field in optional_fields:
            if hasattr(record, field):
                message[field] = getattr(record, field)

        return json.dumps(message)


def configure_logging() -> logging.Logger:
    log_level = getattr(logging, app_config.logging_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    formatter = JsonFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    if app_config.logging_file:
        file_handler = logging.FileHandler(app_config.logging_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if app_config.grafana_cloud_logs_enabled:
        loki_labels = {
            "app": app_config.grafana_cloud_logs_app,
            "env": app_config.environment,
            "service": "discord-bot",
        }
        grafana_handler = GrafanaLokiHandler(
            endpoint=app_config.grafana_cloud_logs_endpoint,
            username=app_config.grafana_cloud_logs_username,
            password=app_config.grafana_cloud_logs_api_key,
            labels=loki_labels,
        )
        grafana_handler.setFormatter(formatter)
        root_logger.addHandler(grafana_handler)

    return logging.getLogger("scyes.bot")
