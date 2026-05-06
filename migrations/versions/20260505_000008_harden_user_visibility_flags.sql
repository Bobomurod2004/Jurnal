-- Migration: 20260505_000008_harden_user_visibility_flags
-- Created: 2026-05-05
-- Description: Ensure users.is_hidden and users.is_blocked always default to false and never remain NULL.

UPDATE public.users
SET is_hidden = FALSE
WHERE is_hidden IS NULL;

UPDATE public.users
SET is_blocked = FALSE
WHERE is_blocked IS NULL;

ALTER TABLE public.users
    ALTER COLUMN is_hidden SET DEFAULT FALSE,
    ALTER COLUMN is_hidden SET NOT NULL,
    ALTER COLUMN is_blocked SET DEFAULT FALSE,
    ALTER COLUMN is_blocked SET NOT NULL;
