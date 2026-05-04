-- Migration: 20260504_000004_add_publication_metadata_fields
-- Created: 2026-05-04
-- Description: Add optional publication metadata fields for position/title/degree/series.

ALTER TABLE publications
    ADD COLUMN IF NOT EXISTS author_position_key TEXT,
    ADD COLUMN IF NOT EXISTS academic_title_key TEXT,
    ADD COLUMN IF NOT EXISTS academic_degree_key TEXT,
    ADD COLUMN IF NOT EXISTS series_key TEXT;
