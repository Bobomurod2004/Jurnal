-- Editor assignments are no longer deleted when a deadline passes.
--
-- The old behaviour ran a hard DELETE, which also cascaded through
-- submission_messages / submission_message_reads / editor_notifications and
-- destroyed the whole admin-editor conversation. Nothing was left to explain
-- why an invitation had vanished. Now the row is parked as `status='expired'`
-- with the moment and reason recorded.
--
-- `status` is plain text with no CHECK constraint, so the new value needs no
-- schema change of its own.

ALTER TABLE editor_assignments
    ADD COLUMN IF NOT EXISTS expired_at bigint;

ALTER TABLE editor_assignments
    ADD COLUMN IF NOT EXISTS expired_reason text;

-- Expired rows are filtered out of the "is this submission still in review?"
-- maths on every submission detail page, so keep that lookup cheap.
CREATE INDEX IF NOT EXISTS idx_editor_assignments_expired_at
    ON editor_assignments (expired_at)
    WHERE expired_at IS NOT NULL;
