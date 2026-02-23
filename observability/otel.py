import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource

# Tracing
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Logging
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor

from config import app_config

def configure_otel() -> None:
    if not app_config.otel_enabled:
        return

    resource = Resource.create(
        {
            "service.name": app_config.otel_service_name,
            "deployment.environment": app_config.environment,
        }
    )

    # Traces
    tracer_provider = TracerProvider(resource=resource)

    span_exporter = OTLPSpanExporter(
        endpoint=app_config.otel_collector_endpoint,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    trace.set_tracer_provider(tracer_provider)

    # Logs
    logger_provider = LoggerProvider(resource=resource)

    log_exporter = OTLPLogExporter(
        endpoint=app_config.otel_collector_endpoint + "/v1/logs",
    )

    logger_provider.add_log_record_processor(
    SimpleLogRecordProcessor(log_exporter)
    )

    set_logger_provider(logger_provider)

    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    logging.getLogger(__name__).info(
        "OTel enabled: %s",
        app_config.otel_collector_endpoint,
    )

def get_tracer():
    return trace.get_tracer("scyes.discord")
