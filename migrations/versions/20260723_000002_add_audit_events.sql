-- Append-only security and operational audit trail used by Grafana's audit dashboard.
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    occurred_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())::bigint,
    service TEXT NOT NULL,
    request_id TEXT,
    actor_id INTEGER,
    actor_role TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id INTEGER,
    method TEXT NOT NULL,
    route TEXT,
    status_code INTEGER NOT NULL,
    remote_addr TEXT,
    user_agent TEXT,
    outcome TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_occurred_at
    ON audit_events (occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_actor_time
    ON audit_events (actor_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_ip_time
    ON audit_events (remote_addr, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_action_time
    ON audit_events (action, occurred_at DESC);
