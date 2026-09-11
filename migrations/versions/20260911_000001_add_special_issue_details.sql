-- Additional metadata and public documents belong only to special issues.
CREATE TABLE IF NOT EXISTS special_issue_details (
    issue_id INTEGER PRIMARY KEY REFERENCES issues(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}'::jsonb
);
