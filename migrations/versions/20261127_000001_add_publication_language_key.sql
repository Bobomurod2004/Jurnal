-- Migration: 20261127_000001_add_publication_language_key
-- Created: 2026-11-27
-- Description: Add language_key (ISO 639-1: uz/ru/en) to publications so
-- Google Scholar metadata reflects the article's own language, not the UI's.

ALTER TABLE publications
    ADD COLUMN IF NOT EXISTS language_key TEXT;
