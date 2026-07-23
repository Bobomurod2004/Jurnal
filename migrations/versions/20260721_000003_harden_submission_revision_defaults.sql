-- Migration: 20260721_000003_harden_submission_revision_defaults
-- Created: 2026-07-21
-- Description: The revision-tracking columns added in 20260721_000001 can
-- end up without their DEFAULT if a runtime schema-sync (dev-only
-- convenience, see SUBMISSION_EXTRA_COLUMN_TYPES) happens to add the bare
-- column first -- ADD COLUMN IF NOT EXISTS is then a no-op and silently
-- keeps the weaker definition. Harden the DEFAULT here so new rows always
-- get a value; backfill existing rows so nothing app-visible changes.
--
-- The backfill UPDATE is scoped to rows whose user_id actually exists,
-- because updating ANY column on a row re-validates ALL of that row's
-- constraints -- including the pre-existing NOT VALID fk_submissions_user
-- constraint -- and this database has at least one legacy orphaned
-- submission (user_id with no matching user) that predates that
-- constraint. That row is left alone; it is unrelated to this migration.
-- NOT NULL is intentionally not added: no other column on this table has
-- it either, and the application already treats these columns
-- defensively (`_parse_int(x) or 1`-style) rather than relying on it.

UPDATE submissions s SET revision_number = 1
WHERE s.revision_number IS NULL
  AND EXISTS (SELECT 1 FROM users u WHERE u.id = s.user_id);

UPDATE submissions s SET revision_allowed = true
WHERE s.revision_allowed IS NULL
  AND EXISTS (SELECT 1 FROM users u WHERE u.id = s.user_id);

UPDATE editor_assignments ea SET revision_round = 1
WHERE ea.revision_round IS NULL
  AND EXISTS (SELECT 1 FROM submissions s WHERE s.id = ea.submission_id);

ALTER TABLE submissions ALTER COLUMN revision_number SET DEFAULT 1;
ALTER TABLE submissions ALTER COLUMN revision_allowed SET DEFAULT true;
ALTER TABLE editor_assignments ALTER COLUMN revision_round SET DEFAULT 1;
