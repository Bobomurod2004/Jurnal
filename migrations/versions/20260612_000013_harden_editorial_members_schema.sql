CREATE TABLE IF NOT EXISTS editorial_members (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    full_name_uz TEXT,
    full_name_ru TEXT,
    position TEXT,
    position_uz TEXT,
    position_ru TEXT,
    organization TEXT,
    organization_uz TEXT,
    organization_ru TEXT,
    biography TEXT,
    biography_uz TEXT,
    biography_ru TEXT,
    country TEXT,
    country_uz TEXT,
    country_ru TEXT,
    country_code TEXT,
    research_interests TEXT,
    research_interests_uz TEXT,
    research_interests_ru TEXT,
    image TEXT,
    member_type TEXT DEFAULT 'editorial_board',
    email TEXT,
    orcid TEXT,
    google_scholar_url TEXT,
    scopus_author_id TEXT,
    scopus_author_url TEXT,
    researcherid TEXT,
    researcherid_url TEXT,
    cv_file TEXT,
    cv_file_uz TEXT,
    cv_file_ru TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at BIGINT DEFAULT EXTRACT(epoch FROM now()),
    updated_at BIGINT,
    created_by INTEGER,
    updated_by INTEGER
);

ALTER TABLE editorial_members
    ADD COLUMN IF NOT EXISTS full_name_uz TEXT,
    ADD COLUMN IF NOT EXISTS full_name_ru TEXT,
    ADD COLUMN IF NOT EXISTS position_uz TEXT,
    ADD COLUMN IF NOT EXISTS position_ru TEXT,
    ADD COLUMN IF NOT EXISTS organization_uz TEXT,
    ADD COLUMN IF NOT EXISTS organization_ru TEXT,
    ADD COLUMN IF NOT EXISTS biography_uz TEXT,
    ADD COLUMN IF NOT EXISTS biography_ru TEXT,
    ADD COLUMN IF NOT EXISTS country TEXT,
    ADD COLUMN IF NOT EXISTS country_uz TEXT,
    ADD COLUMN IF NOT EXISTS country_ru TEXT,
    ADD COLUMN IF NOT EXISTS country_code TEXT,
    ADD COLUMN IF NOT EXISTS research_interests TEXT,
    ADD COLUMN IF NOT EXISTS research_interests_uz TEXT,
    ADD COLUMN IF NOT EXISTS research_interests_ru TEXT,
    ADD COLUMN IF NOT EXISTS image TEXT,
    ADD COLUMN IF NOT EXISTS email TEXT,
    ADD COLUMN IF NOT EXISTS orcid TEXT,
    ADD COLUMN IF NOT EXISTS google_scholar_url TEXT,
    ADD COLUMN IF NOT EXISTS scopus_author_id TEXT,
    ADD COLUMN IF NOT EXISTS scopus_author_url TEXT,
    ADD COLUMN IF NOT EXISTS researcherid TEXT,
    ADD COLUMN IF NOT EXISTS researcherid_url TEXT,
    ADD COLUMN IF NOT EXISTS cv_file TEXT,
    ADD COLUMN IF NOT EXISTS cv_file_uz TEXT,
    ADD COLUMN IF NOT EXISTS cv_file_ru TEXT,
    ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at BIGINT DEFAULT EXTRACT(epoch FROM now()),
    ADD COLUMN IF NOT EXISTS updated_at BIGINT,
    ADD COLUMN IF NOT EXISTS created_by INTEGER,
    ADD COLUMN IF NOT EXISTS updated_by INTEGER;

ALTER TABLE editorial_members
    ALTER COLUMN member_type SET DEFAULT 'editorial_board';

CREATE INDEX IF NOT EXISTS idx_editorial_members_active
    ON editorial_members(is_active);

CREATE INDEX IF NOT EXISTS idx_editorial_members_sort
    ON editorial_members(sort_order, id DESC);

CREATE INDEX IF NOT EXISTS idx_editorial_members_type
    ON editorial_members(member_type);
