-- Migration: 20260522_000011_add_issue_table_of_contents_file
-- Created: 2026-05-22
-- Description: Ensure issues table has table_of_contents_file column for issue TOC uploads.

ALTER TABLE issues
    ADD COLUMN IF NOT EXISTS table_of_contents_file TEXT;
