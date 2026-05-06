-- Migration: 20260505_000005_add_stats_translations
-- Created: 2026-05-05
-- Description: Add translation keys for animated journal statistics bar and sidebar counters.

INSERT INTO translations (alias, content, content_uz, content_ru) VALUES
    ('stat_publications', 'Publications',       'Maqolalar',   'Публикации'),
    ('stat_views',        'Views',              'Ko''rishlar',  'Просмотры'),
    ('stat_downloads',    'Downloads',          'Yuklamalar',  'Загрузки'),
    ('stat_authors',      'Authors',            'Mualliflar',  'Авторы'),
    ('stat_issues',       'Issues',             'Sonlar',      'Выпуски')
ON CONFLICT (alias) DO NOTHING;
