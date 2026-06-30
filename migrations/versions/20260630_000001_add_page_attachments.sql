-- Add file attachments support to pages table for author_instructions
-- Each language can have multiple files stored as JSON array

-- Add attachment columns (JSON arrays of file paths)
ALTER TABLE pages
ADD COLUMN IF NOT EXISTS attachments_en TEXT DEFAULT '[]',
ADD COLUMN IF NOT EXISTS attachments_uz TEXT DEFAULT '[]',
ADD COLUMN IF NOT EXISTS attachments_ru TEXT DEFAULT '[]';

COMMENT ON COLUMN pages.attachments_en IS 'JSON array of file objects: [{"name": "file.pdf", "path": "/uploads/..."}]';
COMMENT ON COLUMN pages.attachments_uz IS 'JSON array of file objects: [{"name": "file.pdf", "path": "/uploads/..."}]';
COMMENT ON COLUMN pages.attachments_ru IS 'JSON array of file objects: [{"name": "file.pdf", "path": "/uploads/..."}]';
