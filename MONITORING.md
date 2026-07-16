# Monitoring and Observability

This repository now ships with a full observability stack for logs, metrics, traces, uptime checks, dashboards, and alerting.

## Stack

- `Grafana 13.1.0`: dashboards, Explore, logs, traces, and alert views
- `Prometheus 3.13.0`: metrics scraping, recording, and alert rule evaluation
- `Alertmanager 0.33.0`: alert routing backend
- `Loki 3.7.3`: log storage
- `Promtail 3.6.11`: Docker log shipping to Loki
- `Tempo 3.0.2`: distributed tracing backend
- `node_exporter 1.11.1`: host CPU, memory, disk, filesystem metrics
- `cAdvisor 0.55.1`: container CPU, memory, filesystem, and restart visibility
- `postgres_exporter 0.20.0`: PostgreSQL metrics
- `blackbox_exporter 0.28.0`: HTTP health and readiness probes

## App instrumentation

Both Flask apps now expose:

- `/metrics`: Prometheus metrics
- `/healthz`: shallow liveness
- `/readyz`: readiness with database check

Both apps now emit:

- structured JSON logs
- request latency metrics
- request counters by route, method, and status
- in-flight request gauges
- exception counters
- OpenTelemetry traces when the observability override compose file is used

Email delivery results are also exported as Prometheus counters through the shared email service.

## Start commands

Production stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build
```

Local stack:

```bash
docker compose -f docker-compose.local.yml -f docker-compose.local.observability.yml up -d --build
```

Useful endpoints:

- Grafana: `http://127.0.0.1:3000`
- Prometheus: `http://127.0.0.1:9090`
- Alertmanager: `http://127.0.0.1:9093`
- Loki: `http://127.0.0.1:3100`
- Tempo: `http://127.0.0.1:3200`

Local override ports use higher host bindings to avoid clashes with already-running developer tools:

- Grafana: `http://127.0.0.1:13000`
- Prometheus: `http://127.0.0.1:19090`
- Alertmanager: `http://127.0.0.1:19093`
- Loki: `http://127.0.0.1:13100`
- Tempo: `http://127.0.0.1:13200`

## Dashboards

Provisioned dashboards:

- `Journal Platform Overview`
- `Journal Logs`
- `Journal Business Overview`

Main things to watch:

- app availability and readiness probes
- request rate, latency, and 5xx responses
- host CPU, memory, and disk
- top containers by CPU and memory
- PostgreSQL uptime and connection pressure
- email delivery failure rate
- submissions, publications, users, activity events, and email outcomes

## Alert rules

Prometheus alert rules are provisioned for:

- service down
- application readiness failure
- Grafana/Loki/Tempo endpoint failure
- high p95 latency
- elevated 5xx rate
- high host CPU
- high host memory
- high root disk usage
- PostgreSQL unavailable
- PostgreSQL connection pressure
- email failures detected

Alertmanager is provisioned with a default receiver placeholder. Replace it with your real email, Slack, Telegram, webhook, or PagerDuty route before relying on notifications in production.

## Environment variables

Important variables:

- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`
- `OBSERVABILITY_METRICS_ENABLED`
- `OTEL_TRACING_ENABLED`
- `OTEL_SERVICE_NAMESPACE`

The observability override compose files inject:

- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://tempo:4318/v1/traces`

You normally do not need to set that manually when starting through the provided compose overrides.

## Notes

- The apps use Gunicorn multi-process Prometheus mode. `PROMETHEUS_MULTIPROC_DIR` is cleaned on each container start.
- Traces are linked from logs through the Loki derived field `trace_id`.
- The PostgreSQL data source in Grafana is provisioned from the same `DB_*` variables used by the apps.
- `Promtail` remains the Docker log shipper in this repository for a predictable Compose-based deployment path. Grafana documents Promtail as end-of-life as of March 2, 2026, so plan a later migration to Grafana Alloy when you want to replace the log collector.

## Recommended operator workflow

1. Open `Journal Platform Overview` and confirm the stack is green.
2. Open `Journal Logs` when a service shows errors or readiness failures.
3. Jump from logs to traces using `trace_id`.
4. Use `Journal Business Overview` to inspect submission and delivery health.
5. Review active alerts in Alertmanager or Grafana before and after deployments.
