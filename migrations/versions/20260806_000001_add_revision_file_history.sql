-- Migration: 20260806_000001_add_revision_file_history
-- Created: 2026-08-06
-- Description: Keep the manuscript files from the version that was replaced
-- during an author revision.  The live submissions row always points at the
-- current version, while this audit record lets editors and administrators
-- see and open the previous version for comparison.

ALTER TABLE submission_revision_log
    ADD COLUMN IF NOT EXISTS file_authors text;

ALTER TABLE submission_revision_log
    ADD COLUMN IF NOT EXISTS file_anonymized text;

CREATE INDEX IF NOT EXISTS idx_submission_revision_log_submission_revision
    ON submission_revision_log(submission_id, revision_number);
