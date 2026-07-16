-- Migration: 20260716_000002_add_home_gallery
-- Created: 2026-07-16
-- Description: Homepage sidebar image gallery managed from fmadmin.
--              Replaces the static "Subscribe" CTA card on the homepage.

CREATE TABLE IF NOT EXISTS public.home_gallery (
    id BIGSERIAL PRIMARY KEY,
    title text,
    title_uz text,
    title_ru text,
    image_path text NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at bigint,
    updated_at bigint
);

CREATE INDEX IF NOT EXISTS idx_home_gallery_active_order
    ON public.home_gallery (is_active, sort_order, id);
