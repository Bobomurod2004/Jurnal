-- Migration: 20260721_000002_add_submission_messages
-- Created: 2026-07-21
-- Description: Two isolated message threads per submission -- author<->admin
-- and admin<->editor (internal, never visible to the author) -- to replace
-- one-way-only notifications with an actual conversation history.

CREATE TABLE IF NOT EXISTS submission_messages (
    id SERIAL PRIMARY KEY,
    submission_id integer NOT NULL,
    visibility_scope text NOT NULL,
    editor_assignment_id integer,
    sender_user_id integer NOT NULL,
    sender_role text NOT NULL,
    body text NOT NULL,
    is_deleted boolean NOT NULL DEFAULT false,
    created_at bigint NOT NULL DEFAULT EXTRACT(epoch FROM now()),
    CONSTRAINT chk_submission_messages_scope CHECK (
        (visibility_scope = 'author_admin' AND editor_assignment_id IS NULL) OR
        (visibility_scope = 'admin_editor' AND editor_assignment_id IS NOT NULL)
    ),
    CONSTRAINT chk_submission_messages_scope_value CHECK (
        visibility_scope IN ('author_admin', 'admin_editor')
    )
);
CREATE INDEX IF NOT EXISTS idx_submission_messages_thread
    ON submission_messages(submission_id, visibility_scope, created_at);
CREATE INDEX IF NOT EXISTS idx_submission_messages_assignment
    ON submission_messages(editor_assignment_id, created_at);

CREATE TABLE IF NOT EXISTS submission_message_reads (
    id SERIAL PRIMARY KEY,
    submission_id integer NOT NULL,
    visibility_scope text NOT NULL,
    editor_assignment_id integer,
    user_id integer NOT NULL,
    last_read_message_id integer,
    last_read_at bigint,
    updated_at bigint
);
-- COALESCE sidesteps NULL-uniqueness: editor_assignment_id is NULL for the
-- author_admin scope, so a plain UNIQUE(submission_id, visibility_scope,
-- editor_assignment_id, user_id) would allow duplicate rows for that scope.
CREATE UNIQUE INDEX IF NOT EXISTS uq_submission_message_reads_thread
    ON submission_message_reads (submission_id, visibility_scope, COALESCE(editor_assignment_id, 0), user_id);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_messages_submission') THEN
        ALTER TABLE submission_messages
            ADD CONSTRAINT fk_submission_messages_submission
            FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_messages_assignment') THEN
        ALTER TABLE submission_messages
            ADD CONSTRAINT fk_submission_messages_assignment
            FOREIGN KEY (editor_assignment_id) REFERENCES editor_assignments(id) ON DELETE CASCADE NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_messages_sender') THEN
        ALTER TABLE submission_messages
            ADD CONSTRAINT fk_submission_messages_sender
            FOREIGN KEY (sender_user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_message_reads_submission') THEN
        ALTER TABLE submission_message_reads
            ADD CONSTRAINT fk_submission_message_reads_submission
            FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_message_reads_assignment') THEN
        ALTER TABLE submission_message_reads
            ADD CONSTRAINT fk_submission_message_reads_assignment
            FOREIGN KEY (editor_assignment_id) REFERENCES editor_assignments(id) ON DELETE CASCADE NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_message_reads_user') THEN
        ALTER TABLE submission_message_reads
            ADD CONSTRAINT fk_submission_message_reads_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;
    END IF;
END $$;
