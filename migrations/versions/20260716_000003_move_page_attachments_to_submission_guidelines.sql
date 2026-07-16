-- Migration: 20260716_000003_move_page_attachments_to_submission_guidelines
-- Created: 2026-07-16
-- Description: Downloadable page attachments belong to the "submission_guidelines"
--              page, not "author_instructions" (they were wired to the wrong alias).
--              Move any already-uploaded attachments over, then clear the old page.

-- Copy attachments into submission_guidelines when it has none of its own.
UPDATE pages sg
SET attachments_en = CASE
        WHEN COALESCE(sg.attachments_en, '[]') IN ('', '[]') THEN COALESCE(ai.attachments_en, '[]')
        ELSE sg.attachments_en
    END,
    attachments_uz = CASE
        WHEN COALESCE(sg.attachments_uz, '[]') IN ('', '[]') THEN COALESCE(ai.attachments_uz, '[]')
        ELSE sg.attachments_uz
    END,
    attachments_ru = CASE
        WHEN COALESCE(sg.attachments_ru, '[]') IN ('', '[]') THEN COALESCE(ai.attachments_ru, '[]')
        ELSE sg.attachments_ru
    END
FROM pages ai
WHERE sg.alias = 'submission_guidelines'
  AND ai.alias = 'author_instructions';

-- Clear the old location only when the target page exists (no data loss otherwise).
UPDATE pages
SET attachments_en = '[]',
    attachments_uz = '[]',
    attachments_ru = '[]'
WHERE alias = 'author_instructions'
  AND EXISTS (SELECT 1 FROM pages WHERE alias = 'submission_guidelines');
