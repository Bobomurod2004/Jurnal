-- Migration: 20260518_000010_add_publication_section_key
-- Created: 2026-05-18
-- Description: Add section_key to publications for article section/rukn metadata.

ALTER TABLE publications
    ADD COLUMN IF NOT EXISTS section_key TEXT;
