-- Migration: 20260507_000009_add_author_profile_name_parts
-- Created: 2026-05-07
-- Description: Add structured name columns for author profiles (second_name, father_name).

ALTER TABLE public.author_profile
    ADD COLUMN IF NOT EXISTS second_name text,
    ADD COLUMN IF NOT EXISTS father_name text;
