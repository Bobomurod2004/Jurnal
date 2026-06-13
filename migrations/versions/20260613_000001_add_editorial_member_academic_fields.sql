ALTER TABLE editorial_members
    ADD COLUMN IF NOT EXISTS academic_degree TEXT,
    ADD COLUMN IF NOT EXISTS academic_degree_uz TEXT,
    ADD COLUMN IF NOT EXISTS academic_degree_ru TEXT,
    ADD COLUMN IF NOT EXISTS academic_title TEXT,
    ADD COLUMN IF NOT EXISTS academic_title_uz TEXT,
    ADD COLUMN IF NOT EXISTS academic_title_ru TEXT;
