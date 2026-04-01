-- Migration: 20260327_000002_add_performance_indexes
-- Created: 2026-03-27
-- Description: Add missing indexes for better query performance

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_rolename ON users(rolename);
CREATE INDEX IF NOT EXISTS idx_users_is_blocked ON users(is_blocked);
CREATE INDEX IF NOT EXISTS idx_users_country_id ON users(country_id);
CREATE INDEX IF NOT EXISTS idx_users_tariff_id ON users(tariff_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Author profile indexes
CREATE INDEX IF NOT EXISTS idx_author_profile_user_id ON author_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_author_profile_email ON author_profile(email);
CREATE INDEX IF NOT EXISTS idx_author_profile_orcid ON author_profile(orcid);

-- Submissions indexes
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_main_author_id ON submissions(main_author_id);
CREATE INDEX IF NOT EXISTS idx_submissions_created_date ON submissions(created_date);
CREATE INDEX IF NOT EXISTS idx_submissions_editor_review_status ON submissions(editor_review_status);

-- Publications indexes
CREATE INDEX IF NOT EXISTS idx_publications_issue_id ON publications(issue_id);
CREATE INDEX IF NOT EXISTS idx_publications_main_author_id ON publications(main_author_id);
CREATE INDEX IF NOT EXISTS idx_publications_stage ON publications(stage);
CREATE INDEX IF NOT EXISTS idx_publications_date_publish ON publications(date_publish);
CREATE INDEX IF NOT EXISTS idx_publications_is_paid ON publications(is_paid);
CREATE INDEX IF NOT EXISTS idx_publications_doi ON publications(doi);

-- Issues indexes
CREATE INDEX IF NOT EXISTS idx_issues_year ON issues(year);
CREATE INDEX IF NOT EXISTS idx_issues_category ON issues(category);
CREATE INDEX IF NOT EXISTS idx_issues_is_paid ON issues(is_paid);

-- Payments indexes
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);

-- News indexes
CREATE INDEX IF NOT EXISTS idx_news_author_id ON news(author_id);
CREATE INDEX IF NOT EXISTS idx_news_status ON news(status);
CREATE INDEX IF NOT EXISTS idx_news_type ON news(type);
CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at);
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news(published_at);

-- Files indexes
CREATE INDEX IF NOT EXISTS idx_files_upload_time ON files(upload_time);

-- Publication related indexes
CREATE INDEX IF NOT EXISTS idx_publication_citations_publication_id ON publication_citations(publication_id);
CREATE INDEX IF NOT EXISTS idx_publication_figures_publication_id ON publication_figures(publication_id);
CREATE INDEX IF NOT EXISTS idx_publication_parts_publication_id ON publication_parts(publication_id);
CREATE INDEX IF NOT EXISTS idx_publication_refs_publication_id ON publication_refs(publication_id);

-- Tariffs indexes
CREATE INDEX IF NOT EXISTS idx_tariffs_is_default ON tariffs(is_default);
CREATE INDEX IF NOT EXISTS idx_tariffs_is_verified ON tariffs(is_verified);

-- Translations indexes
CREATE INDEX IF NOT EXISTS idx_translations_alias ON translations(alias);

-- Pages indexes
CREATE INDEX IF NOT EXISTS idx_pages_alias ON pages(alias);

-- Settings indexes
CREATE INDEX IF NOT EXISTS idx_settings_k ON settings(k);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_submissions_user_status ON submissions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_publications_issue_stage ON publications(issue_id, stage);
CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_id, status);
CREATE INDEX IF NOT EXISTS idx_news_status_created ON news(status, created_at);

-- GIN indexes for array fields (if using PostgreSQL array operations)
CREATE INDEX IF NOT EXISTS idx_submissions_keywords ON submissions USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_submissions_classifications ON submissions USING GIN(classifications);
CREATE INDEX IF NOT EXISTS idx_publications_keywords ON publications USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_publications_file_ids ON publications USING GIN(file_ids);
