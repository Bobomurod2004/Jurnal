-- Migration: 20260505_000007_add_publication_page_range
-- Created: 2026-05-05
-- Description: Add page range field for publications (e.g. 7-26).

ALTER TABLE public.publications
    ADD COLUMN IF NOT EXISTS page_range TEXT;
