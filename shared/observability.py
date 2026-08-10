import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Optional, Tuple

from flask import Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    generate_latest,
    multiprocess,
)

try:
    import psycopg2
except ImportError:  # pragma: no cover - import-time safety
    psycopg2 = None

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_NAMESPACE, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except ImportError:  # pragma: no cover - import-time safety
    trace = None
    OTLPSpanExporter = None
    FlaskInstrumentor = None
    Psycopg2Instrumentor = None
    RequestsInstrumentor = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    SERVICE_NAME = "service.name"
    SERVICE_NAMESPACE = "service.namespace"
    SERVICE_VERSION = "service.version"


_LOGGING_LOCK = threading.Lock()
_TRACING_LOCK = threading.Lock()
_LIBRARY_BOOTSTRAP_LOCK = threading.Lock()
_LIBRARIES_BOOTSTRAPPED = False
_REQUESTS_INSTRUMENTED = False

_HTTP_REQUESTS_TOTAL = Counter(
    "journal_http_requests_total",
    "Total HTTP requests handled by the Flask services.",
    ["service", "method", "route", "status_code"],
)
_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "journal_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["service", "method", "route"],
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)
_HTTP_REQUEST_EXCEPTIONS_TOTAL = Counter(
    "journal_http_request_exceptions_total",
    "Unhandled HTTP request exceptions.",
    ["service", "method", "route", "exception_type"],
)
_HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "journal_http_requests_in_progress",
    "In-flight HTTP requests across all workers.",
    ["service"],
    multiprocess_mode="livesum",
)
_APP_INFO = Gauge(
    "journal_app_info",
    "Static metadata about the running Flask service.",
    ["service", "version"],
    multiprocess_mode="max",
)
_API_ROUTE_INFO = Gauge(
    "journal_api_route_info",
    "Inventory of registered API routes; a value of 1 means the route is available.",
    ["service", "method", "route"],
    multiprocess_mode="max",
)
_DEPENDENCY_HEALTH = Gauge(
    "journal_dependency_health",
    "Dependency health state where 1=healthy and 0=unhealthy.",
    ["service", "dependency"],
    multiprocess_mode="max",
)
_EMAIL_DELIVERY_TOTAL = Counter(
    "journal_email_delivery_total",
    "Email delivery attempts recorded by application and outcome.",
    ["app_name", "status"],
)
_AUDIT_EVENTS_TOTAL = Counter(
    "journal_audit_events_total",
    "Security and operational audit events recorded by action and outcome.",
    ["service", "action", "outcome"],
)


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def _should_enable_metrics() -> bool:
    return _env_flag("OBSERVABILITY_METRICS_ENABLED", True)


def _should_enable_tracing() -> bool:
    endpoint = (
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or ""
    ).strip()
    return _env_flag("OTEL_TRACING_ENABLED", bool(endpoint))


def _otlp_traces_endpoint() -> str:
    endpoint = (
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or ""
    ).strip()
    if not endpoint:
        return ""
    if endpoint.endswith("/v1/traces"):
        return endpoint
    return endpoint.rstrip("/") + "/v1/traces"


def _safe_json_object(raw_message: str) -> Optional[dict]:
    text = str(raw_message or "").strip()
    if not text.startswith("{") or not text.endswith("}"):
        return None
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def current_trace_context() -> Tuple[str, str]:
    if trace is None:
        return "", ""
    try:
        span = trace.get_current_span()
        context = span.get_span_context() if span else None
        if not context or not context.is_valid:
            return "", ""
        return f"{context.trace_id:032x}", f"{context.span_id:016x}"
    except Exception:
        return "", ""


class StructuredJsonFormatter(logging.Formatter):
    def __init__(self, service_name: str, version: str):
        super().__init__()
        self.service_name = service_name
        self.version = version

    def format(self, record: logging.LogRecord) -> str:
        payload = _safe_json_object(record.getMessage()) or {
            "message": record.getMessage(),
        }
        payload.setdefault(
            "timestamp",
            datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        )
        payload.setdefault("level", record.levelname.upper())
        payload.setdefault("logger", record.name)
        payload.setdefault("service", self.service_name)
        payload.setdefault("version", self.version)
        payload.setdefault("process", record.process)
        payload.setdefault("thread", record.threadName)

        trace_id, span_id = current_trace_context()
        if trace_id:
            payload.setdefault("trace_id", trace_id)
        if span_id:
            payload.setdefault("span_id", span_id)

        if record.exc_info:
            payload.setdefault("exception", self.formatException(record.exc_info))

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(app, service_name: str, version: str, level_name: str) -> None:
    with _LOGGING_LOCK:
        level = getattr(logging, str(level_name or "INFO").upper(), logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter(service_name=service_name, version=version))

        root_logger = logging.getLogger()
        root_logger.handlers = [handler]
        root_logger.setLevel(level)

        app.logger.handlers = []
        app.logger.propagate = True
        app.logger.setLevel(level)

        for logger_name in ("gunicorn.error", "werkzeug"):
            child_logger = logging.getLogger(logger_name)
            child_logger.handlers = []
            child_logger.propagate = True
            child_logger.setLevel(level)

        # gunicorn.access duplicates every line the app's own `log_request`
        # hook already writes -- same request, same status, but without the
        # request_id, user or duration. Routing it here doubled the volume
        # shipped to Loki for no extra information. Silenced at the logger, not
        # via --access-logfile, because this handler would keep emitting it.
        access_logger = logging.getLogger("gunicorn.access")
        access_logger.handlers = []
        access_logger.propagate = False
        access_logger.disabled = True

        logging.captureWarnings(True)


def bootstrap_telemetry_libraries() -> None:
    global _LIBRARIES_BOOTSTRAPPED
    if _LIBRARIES_BOOTSTRAPPED or not _should_enable_tracing():
        return
    if Psycopg2Instrumentor is None:
        return

    with _LIBRARY_BOOTSTRAP_LOCK:
        if _LIBRARIES_BOOTSTRAPPED:
            return
        try:
            Psycopg2Instrumentor().instrument()
        except Exception:
            pass
        _LIBRARIES_BOOTSTRAPPED = True


def configure_tracing(app, service_name: str, version: str) -> None:
    global _REQUESTS_INSTRUMENTED

    if not _should_enable_tracing() or TracerProvider is None:
        return

    endpoint = _otlp_traces_endpoint()
    if not endpoint:
        return

    with _TRACING_LOCK:
        tracer_provider = trace.get_tracer_provider() if trace is not None else None
        if not isinstance(tracer_provider, TracerProvider):
            resource = Resource.create(
                {
                    SERVICE_NAME: service_name,
                    SERVICE_NAMESPACE: os.getenv("OTEL_SERVICE_NAMESPACE", "journal"),
                    SERVICE_VERSION: version,
                }
            )
            tracer_provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=endpoint)
            tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(tracer_provider)

        if not _REQUESTS_INSTRUMENTED and RequestsInstrumentor is not None:
            try:
                RequestsInstrumentor().instrument()
                _REQUESTS_INSTRUMENTED = True
            except Exception:
                pass

        if FlaskInstrumentor is not None:
            instrumentor = FlaskInstrumentor()
            if not instrumentor.is_instrumented_by_opentelemetry:
                instrumentor.instrument_app(
                    app,
                    excluded_urls=r"/metrics,/healthz,/readyz",
                )


def _default_route_label() -> str:
    url_rule = getattr(request, "url_rule", None)
    if url_rule is not None and getattr(url_rule, "rule", None):
        return url_rule.rule
    endpoint = (request.endpoint or "").strip()
    if endpoint:
        return endpoint
    if request.path:
        return request.path
    return "unmatched"


def _build_metrics_registry() -> CollectorRegistry:
    multiprocess_dir = (os.getenv("PROMETHEUS_MULTIPROC_DIR") or "").strip()
    if multiprocess_dir:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry
    return REGISTRY


def legacy_postgres_healthcheck(connector) -> Tuple[bool, str]:
    conn = getattr(connector, "conn", None)
    if conn is None:
        return False, "connection_not_initialized"

    connection_errors = ()
    if psycopg2 is not None:
        connection_errors = (psycopg2.InterfaceError, psycopg2.OperationalError)

    for attempt in range(2):
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.commit()
            return True, "ok"
        except connection_errors:
            try:
                connector._connect()
                conn = getattr(connector, "conn", None)
            except Exception as exc:
                return False, str(exc)
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, str(exc)
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    return False, f"retry_exhausted_after_{attempt + 1}_attempts"


def _set_dependency_health(service_name: str, dependency_name: str, is_healthy: bool) -> None:
    _DEPENDENCY_HEALTH.labels(service=service_name, dependency=dependency_name).set(1 if is_healthy else 0)


def attach_metrics_and_health(
    app,
    service_name: str,
    version: str,
    db_healthcheck: Optional[Callable[[], Tuple[bool, str]]] = None,
) -> None:
    if not _should_enable_metrics():
        return

    _APP_INFO.labels(service=service_name, version=version).set(1)

    @app.before_request
    def _observability_before_request():
        g._observability_start = time.perf_counter()
        _HTTP_REQUESTS_IN_PROGRESS.labels(service=service_name).inc()

    @app.after_request
    def _observability_after_request(response):
        try:
            route = _default_route_label()
            started_at = getattr(g, "_observability_start", None)
            duration = 0.0
            if isinstance(started_at, (int, float)):
                duration = max(0.0, time.perf_counter() - started_at)

            if request.path not in {"/metrics"}:
                _HTTP_REQUESTS_TOTAL.labels(
                    service=service_name,
                    method=request.method,
                    route=route,
                    status_code=str(response.status_code),
                ).inc()
                _HTTP_REQUEST_DURATION_SECONDS.labels(
                    service=service_name,
                    method=request.method,
                    route=route,
                ).observe(duration)
        finally:
            _HTTP_REQUESTS_IN_PROGRESS.labels(service=service_name).dec()
        return response

    @app.teardown_request
    def _observability_teardown(exception):
        if exception is None:
            return None
        _HTTP_REQUEST_EXCEPTIONS_TOTAL.labels(
            service=service_name,
            method=request.method,
            route=_default_route_label(),
            exception_type=exception.__class__.__name__,
        ).inc()
        return None

    @app.get("/readyz")
    def readyz():
        checks = {"application": "ok"}
        is_ready = True

        if db_healthcheck is not None:
            db_ok, detail = db_healthcheck()
            checks["database"] = detail if not db_ok else "ok"
            _set_dependency_health(service_name, "database", db_ok)
            is_ready = is_ready and db_ok

        status_code = 200 if is_ready else 503
        payload = {
            "status": "ok" if is_ready else "degraded",
            "service": service_name,
            "version": version,
            "checks": checks,
        }
        return jsonify(payload), status_code

    @app.get("/metrics")
    def metrics():
        if db_healthcheck is not None:
            db_ok, _detail = db_healthcheck()
            _set_dependency_health(service_name, "database", db_ok)
        registry = _build_metrics_registry()
        return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


def register_api_route_inventory(app, service_name: str) -> None:
    """Expose every registered application API route, including unused routes.

    Request counters only exist after a route receives traffic.  This inventory
    lets Grafana distinguish an unused API (0 attempts) from a missing API.
    """
    for rule in app.url_map.iter_rules():
        route = str(rule.rule or '')
        if not (route.startswith('/api/') or route.startswith('/fmadmin/api/')):
            continue
        for method in sorted(set(rule.methods or ()) - {'HEAD', 'OPTIONS'}):
            _API_ROUTE_INFO.labels(
                service=service_name,
                method=method,
                route=route,
            ).set(1)


def record_email_delivery_metric(app_name: str, status: str) -> None:
    normalized_app_name = str(app_name or "unknown").strip() or "unknown"
    normalized_status = str(status or "unknown").strip().lower() or "unknown"
    _EMAIL_DELIVERY_TOTAL.labels(
        app_name=normalized_app_name,
        status=normalized_status,
    ).inc()


def record_audit_event_metric(service: str, action: str, outcome: str) -> None:
    _AUDIT_EVENTS_TOTAL.labels(
        service=str(service or 'unknown').strip() or 'unknown',
        action=str(action or 'unknown').strip() or 'unknown',
        outcome=str(outcome or 'unknown').strip() or 'unknown',
    ).inc()
