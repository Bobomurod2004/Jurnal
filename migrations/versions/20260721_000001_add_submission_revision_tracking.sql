-- Migration: 20260721_000001_add_submission_revision_tracking
-- Created: 2026-07-21
-- Description: Track revision cycles on submissions so a rejected article can be
-- fixed and resubmitted on the SAME row instead of creating a disconnected new one.

ALTER TABLE submissions ADD COLUMN IF NOT EXISTS revision_number integer NOT NULL DEFAULT 1;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS rejection_origin text;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS rejected_at bigint;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS rejected_by integer;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS revision_allowed boolean NOT NULL DEFAULT true;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS last_revision_submitted_at bigint;

ALTER TABLE editor_assignments ADD COLUMN IF NOT EXISTS revision_round integer NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS submission_revision_log (
    id SERIAL PRIMARY KEY,
    submission_id integer NOT NULL,
    revision_number integer NOT NULL,
    rejection_origin text,
    rejected_by integer,
    rejected_at bigint,
    rejection_notes text,
    resubmitted_at bigint,
    resubmitted_by integer,
    created_at bigint DEFAULT EXTRACT(epoch FROM now())
);
CREATE INDEX IF NOT EXISTS idx_submission_revision_log_submission_id ON submission_revision_log(submission_id);

-- Best-effort backfill for submissions rejected before this migration existed:
-- we can't know the exact stage they were rejected from, so infer the closest
-- one from current data (has a reviewed/rejected editor assignment -> in_review,
-- else has an anti-plagiarism file -> anti_plagiarism, else technical_check).
-- `anti_plagiarism_file` and `editor_assignments.status` are added at app
-- runtime (not in the base schema), so on a brand-new install this migration
-- can run before those columns exist -- guard with dynamic SQL and fall back
-- to a plain 'technical_check' default (safe: a fresh install has no real
-- rejection history to preserve anyway).
DO $$
DECLARE
    has_antiplag_col boolean;
    has_assignment_status_col boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'submissions' AND column_name = 'anti_plagiarism_file'
    ) INTO has_antiplag_col;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'editor_assignments' AND column_name = 'status'
    ) INTO has_assignment_status_col;

    IF has_antiplag_col AND has_assignment_status_col THEN
        UPDATE submissions s
        SET rejection_origin = COALESCE(
            (
                SELECT 'in_review'
                FROM editor_assignments ea
                WHERE ea.submission_id = s.id AND ea.status IN ('reviewed', 'rejected')
                LIMIT 1
            ),
            CASE WHEN s.anti_plagiarism_file IS NOT NULL THEN 'anti_plagiarism' END,
            'technical_check'
        )
        WHERE s.status = 'rejected' AND s.rejection_origin IS NULL;
    ELSIF has_antiplag_col THEN
        UPDATE submissions s
        SET rejection_origin = CASE WHEN s.anti_plagiarism_file IS NOT NULL THEN 'anti_plagiarism' ELSE 'technical_check' END
        WHERE s.status = 'rejected' AND s.rejection_origin IS NULL;
    ELSE
        UPDATE submissions s
        SET rejection_origin = 'technical_check'
        WHERE s.status = 'rejected' AND s.rejection_origin IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_revision_log_submission') THEN
        ALTER TABLE submission_revision_log
            ADD CONSTRAINT fk_submission_revision_log_submission
            FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_revision_log_rejected_by') THEN
        ALTER TABLE submission_revision_log
            ADD CONSTRAINT fk_submission_revision_log_rejected_by
            FOREIGN KEY (rejected_by) REFERENCES users(id) ON DELETE SET NULL NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_revision_log_resubmitted_by') THEN
        ALTER TABLE submission_revision_log
            ADD CONSTRAINT fk_submission_revision_log_resubmitted_by
            FOREIGN KEY (resubmitted_by) REFERENCES users(id) ON DELETE SET NULL NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submissions_rejected_by') THEN
        ALTER TABLE submissions
            ADD CONSTRAINT fk_submissions_rejected_by
            FOREIGN KEY (rejected_by) REFERENCES users(id) ON DELETE SET NULL NOT VALID;
    END IF;
END $$;
