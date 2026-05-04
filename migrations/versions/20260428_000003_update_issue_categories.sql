-- Migration: 20260428_000003_update_issue_categories
-- Created: 2026-04-28
-- Description: Ensure issue categories include masters, doctoral, professor-teacher, and special in 3 languages.

UPDATE fix_issue_categories
SET
    name = 'Series: Master''s',
    name_uz = 'Seriya: Magistratura',
    name_ru = 'Серия: Магистратура'
WHERE alias = 'masters';

INSERT INTO fix_issue_categories (alias, name, name_uz, name_ru)
SELECT
    'masters',
    'Series: Master''s',
    'Seriya: Magistratura',
    'Серия: Магистратура'
WHERE NOT EXISTS (
    SELECT 1 FROM fix_issue_categories WHERE alias = 'masters'
);

UPDATE fix_issue_categories
SET
    name = 'Series: Doctoral',
    name_uz = 'Seriya: Doktorantura',
    name_ru = 'Серия: Докторантура'
WHERE alias = 'phd';

INSERT INTO fix_issue_categories (alias, name, name_uz, name_ru)
SELECT
    'phd',
    'Series: Doctoral',
    'Seriya: Doktorantura',
    'Серия: Докторантура'
WHERE NOT EXISTS (
    SELECT 1 FROM fix_issue_categories WHERE alias = 'phd'
);

UPDATE fix_issue_categories
SET
    name = 'Series: Professors & Teachers',
    name_uz = 'Seriya: Professor-o''qituvchilar',
    name_ru = 'Серия: Профессора-преподаватели'
WHERE alias = 'teacher';

INSERT INTO fix_issue_categories (alias, name, name_uz, name_ru)
SELECT
    'teacher',
    'Series: Professors & Teachers',
    'Seriya: Professor-o''qituvchilar',
    'Серия: Профессора-преподаватели'
WHERE NOT EXISTS (
    SELECT 1 FROM fix_issue_categories WHERE alias = 'teacher'
);

UPDATE fix_issue_categories
SET
    name = 'Special Issue',
    name_uz = 'Maxsus son',
    name_ru = 'Специальный выпуск'
WHERE alias = 'special';

INSERT INTO fix_issue_categories (alias, name, name_uz, name_ru)
SELECT
    'special',
    'Special Issue',
    'Maxsus son',
    'Специальный выпуск'
WHERE NOT EXISTS (
    SELECT 1 FROM fix_issue_categories WHERE alias = 'special'
);
