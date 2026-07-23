-- Migration: 20260722_000001_consolidate_submission_status
-- Created: 2026-07-22
-- Description: Consolidate submissions.status + workflow_stage +
-- editor_review_status + rejection_origin into a single canonical 11-value
-- status enum (see shared/submission_status.py). The status value alone now
-- carries both "where in the pipeline" and "why" -- e.g. failed_technical_check
-- vs revision_required vs rejected are three distinct, resubmit-aware
-- outcomes instead of one generic 'rejected' + a separate origin flag.
--
-- workflow_stage / editor_review_status / rejection_origin / revision_allowed
-- columns are deliberately NOT dropped here -- application code stops
-- reading/writing them as of this change, but they are kept in place for a
-- safe rollback window. A later, separate migration can drop them once
-- confidence is established.
--
-- 'draft' is untouched: it is a pre-submission state outside this enum,
-- exactly as before (submissions lists already filter it out everywhere).

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'submissions' AND column_name = 'workflow_stage'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'submissions' AND column_name = 'rejection_origin'
    ) THEN
        UPDATE submissions SET status = CASE
            WHEN status = 'draft' THEN 'draft'
            WHEN status = 'rejected' AND rejection_origin = 'in_review' THEN 'revision_required'
            WHEN status = 'rejected' AND COALESCE(rejection_origin, '') IN ('waiting', 'technical_check', '') THEN 'failed_technical_check'
            WHEN status = 'rejected' THEN 'rejected'
            WHEN COALESCE(workflow_stage, '') = 'published' OR status = 'published' THEN 'published'
            WHEN COALESCE(workflow_stage, '') = 'payment' THEN 'payment_pending'
            WHEN COALESCE(workflow_stage, '') = 'recommended' THEN 'recommended'
            WHEN COALESCE(workflow_stage, '') = 'in_review' THEN 'under_review'
            WHEN COALESCE(workflow_stage, '') = 'anti_plagiarism' THEN 'plagiarism_check'
            WHEN COALESCE(workflow_stage, '') = 'waiting' THEN 'pending'
            WHEN workflow_stage IS NULL AND editor_review_status = 'approved' THEN 'recommended'
            WHEN workflow_stage IS NULL AND editor_review_status IN ('reviewed', 'in_review', 'assigned') THEN 'under_review'
            WHEN status IN ('submitted', 'pending', 'in_process') THEN 'pending'
            ELSE status
        END
        -- Deliberately no "already migrated?" WHERE guard: 'rejected' and
        -- 'pending' are both old-vocabulary values AND new canonical values,
        -- so filtering on the target status would wrongly skip rows whose
        -- old status was already the string 'rejected'/'pending' -- exactly
        -- the ones that most need re-deriving from rejection_origin /
        -- workflow_stage. Re-deriving unconditionally is safe and idempotent
        -- since this UPDATE never modifies workflow_stage/rejection_origin/
        -- editor_review_status themselves.
        WHERE status <> 'draft';
    END IF;
END $$;
