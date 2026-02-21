import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

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
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=app_config.otel_collector_endpoint,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    logging.getLogger(__name__).info(
        "OTel tracing enabled with collector endpoint %s",
        app_config.otel_collector_endpoint,
    )


tracer = trace.get_tracer("scyes.discord")
