-- Rename the Uzbek home-gallery heading shown on the public homepage.
-- The database value takes precedence over the local fallback translation.
UPDATE translations
SET content_uz = 'INFOGRAFIKA'
WHERE alias = 'home_gallery_title';
