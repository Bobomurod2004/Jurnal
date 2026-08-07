-- Migration: 20260806_000002_revision_review_workflow
-- Keep each correction cycle explicit and require a fresh anti-plagiarism
-- check only when the editor/admin marked the expected changes as material.

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS revision_requires_antiplagiarism_recheck boolean NOT NULL DEFAULT false;

ALTER TABLE submission_revision_rounds
    ADD COLUMN IF NOT EXISTS requires_antiplagiarism_recheck boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS feedback_comments text,
    ADD COLUMN IF NOT EXISTS feedback_files text[] NOT NULL DEFAULT '{}'::text[];

CREATE INDEX IF NOT EXISTS idx_editor_assignments_submission_revision_round
    ON editor_assignments(submission_id, revision_round);
