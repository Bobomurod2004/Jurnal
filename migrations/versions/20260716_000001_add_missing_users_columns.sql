-- Migration: 20260716_000001_add_missing_users_columns
-- Created: 2026-07-16
-- Description: Add users columns that were previously created only by the runtime
--              schema sync (disabled in production by default). Without them the
--              registration flow fails with "Table has not column ui_language".

ALTER TABLE public.users ADD COLUMN IF NOT EXISTS ui_language text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS roles text[];
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_hidden boolean;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS oauth_provider text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS oauth_sub text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS oauth_email_verified boolean;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS oauth_last_login_at bigint;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS admin_tracks text[];
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS editor_admin_id integer;

-- Keep account state flags deterministic (mirrors the runtime sync behaviour).
UPDATE public.users
SET is_hidden = FALSE
WHERE is_hidden IS NULL;

ALTER TABLE public.users
    ALTER COLUMN is_hidden SET DEFAULT FALSE,
    ALTER COLUMN is_hidden SET NOT NULL;

UPDATE public.users
SET is_blocked = FALSE
WHERE is_blocked IS NULL;

ALTER TABLE public.users
    ALTER COLUMN is_blocked SET DEFAULT FALSE,
    ALTER COLUMN is_blocked SET NOT NULL;

-- Backfill roles from the legacy rolename column.
UPDATE public.users
SET roles = ARRAY[LOWER(COALESCE(NULLIF(TRIM(rolename), ''), 'user'))]::text[]
WHERE roles IS NULL OR COALESCE(array_length(roles, 1), 0) = 0;
