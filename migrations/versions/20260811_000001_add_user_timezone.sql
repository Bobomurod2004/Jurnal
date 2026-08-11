-- Per-user display timezone (IANA name, e.g. 'Europe/Berlin'). NULL means
-- "not detected yet" -- every caller falls back to the existing global
-- Tashkent default (shared/user_timezone.py), so existing users see zero
-- change in what they're shown until their browser reports a real zone.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS timezone_name text;
