-- Publication URL the admin attaches to a submission once it is marked
-- 'published', so the author's dashboard and the "published" email/notification
-- can link straight to the live article instead of the generic articles list.
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS published_url text;
