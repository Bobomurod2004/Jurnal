ALTER TABLE editorial_members
    ADD COLUMN IF NOT EXISTS country TEXT,
    ADD COLUMN IF NOT EXISTS country_uz TEXT,
    ADD COLUMN IF NOT EXISTS country_ru TEXT,
    ADD COLUMN IF NOT EXISTS country_code TEXT,
    ADD COLUMN IF NOT EXISTS research_interests TEXT,
    ADD COLUMN IF NOT EXISTS research_interests_uz TEXT,
    ADD COLUMN IF NOT EXISTS research_interests_ru TEXT,
    ADD COLUMN IF NOT EXISTS scopus_author_id TEXT,
    ADD COLUMN IF NOT EXISTS scopus_author_url TEXT,
    ADD COLUMN IF NOT EXISTS researcherid TEXT,
    ADD COLUMN IF NOT EXISTS researcherid_url TEXT;
