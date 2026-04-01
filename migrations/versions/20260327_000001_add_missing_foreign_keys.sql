-- Migration: 20260327_000001_add_missing_foreign_keys
-- Created: 2026-03-27
-- Description: Add missing foreign key constraints to ensure data integrity

DO $$
BEGIN
    -- Use NOT VALID so legacy rows do not block deployment/bootstrap.
    -- New/updated rows will still be checked by these constraints.
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_author_profile_user') THEN
        ALTER TABLE author_profile
            ADD CONSTRAINT fk_author_profile_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submissions_user') THEN
        ALTER TABLE submissions
            ADD CONSTRAINT fk_submissions_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submissions_main_author') THEN
        ALTER TABLE submissions
            ADD CONSTRAINT fk_submissions_main_author
            FOREIGN KEY (main_author_id) REFERENCES author_profile(id) ON DELETE SET NULL NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_publications_issue') THEN
        ALTER TABLE publications
            ADD CONSTRAINT fk_publications_issue
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE SET NULL NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_publications_main_author') THEN
        ALTER TABLE publications
            ADD CONSTRAINT fk_publications_main_author
            FOREIGN KEY (main_author_id) REFERENCES author_profile(id) ON DELETE SET NULL NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_payments_user') THEN
        ALTER TABLE payments
            ADD CONSTRAINT fk_payments_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_citations_publication') THEN
        ALTER TABLE publication_citations
            ADD CONSTRAINT fk_citations_publication
            FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_figures_publication') THEN
        ALTER TABLE publication_figures
            ADD CONSTRAINT fk_figures_publication
            FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_parts_publication') THEN
        ALTER TABLE publication_parts
            ADD CONSTRAINT fk_parts_publication
            FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_refs_publication') THEN
        ALTER TABLE publication_refs
            ADD CONSTRAINT fk_refs_publication
            FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'files' AND column_name = 'user_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_files_user'
    ) THEN
        ALTER TABLE files
            ADD CONSTRAINT fk_files_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_news_author') THEN
        ALTER TABLE news
            ADD CONSTRAINT fk_news_author
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL NOT VALID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_doc_uploads_user') THEN
        ALTER TABLE user_doc_uploads
            ADD CONSTRAINT fk_doc_uploads_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT VALID;
    END IF;

    -- address_country is text in db_schema.sql, so only add this FK if schema is compatible.
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'author_profile'
          AND column_name = 'address_country'
          AND data_type = 'integer'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_author_profile_country'
    ) THEN
        ALTER TABLE author_profile
            ADD CONSTRAINT fk_author_profile_country
            FOREIGN KEY (address_country) REFERENCES fix_country(id) ON DELETE SET NULL NOT VALID;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users'
          AND column_name = 'country_id'
          AND data_type = 'integer'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_country'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT fk_users_country
            FOREIGN KEY (country_id) REFERENCES fix_country(id) ON DELETE SET NULL NOT VALID;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'email'
    ) AND NOT EXISTS (
        SELECT 1 FROM users WHERE email IS NULL
    ) THEN
        ALTER TABLE users
            ALTER COLUMN email SET NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'submissions' AND column_name = 'user_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM submissions WHERE user_id IS NULL
    ) THEN
        ALTER TABLE submissions
            ALTER COLUMN user_id SET NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'publications' AND column_name = 'title'
    ) AND NOT EXISTS (
        SELECT 1 FROM publications WHERE title IS NULL
    ) THEN
        ALTER TABLE publications
            ALTER COLUMN title SET NOT NULL;
    END IF;
END $$;
