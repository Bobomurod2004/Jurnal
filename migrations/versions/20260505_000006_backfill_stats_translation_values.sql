-- Migration: 20260505_000006_backfill_stats_translation_values
-- Created: 2026-05-05
-- Description: Backfill localized values for stats aliases that may already exist as placeholders.

INSERT INTO translations (alias, content, content_uz, content_ru)
VALUES
    ('stat_publications', 'Publications', 'Maqolalar', 'Публикации'),
    ('stat_views', 'Views', 'Ko''rishlar', 'Просмотры'),
    ('stat_downloads', 'Downloads', 'Yuklamalar', 'Загрузки'),
    ('stat_authors', 'Authors', 'Mualliflar', 'Авторы'),
    ('stat_issues', 'Issues', 'Sonlar', 'Выпуски'),
    ('journal_metrics', 'Journal metrics', 'Jurnal ko''rsatkichlari', 'Показатели журнала')
ON CONFLICT (alias) DO UPDATE SET
    content = EXCLUDED.content,
    content_uz = EXCLUDED.content_uz,
    content_ru = EXCLUDED.content_ru;
