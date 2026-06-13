-- Add initial contact info to settings table
-- Idempotent: uses ON CONFLICT (k) DO NOTHING

INSERT INTO settings (k, v, created_at)
VALUES (
    'contact_persons',
    '[{"name": "Bakieva Gulandom Khisomovna", "position": "Editor-in-Chief", "email": "philologymatters@uzswlu.uz", "phone": ""}, {"name": "Kakharova Iroda Sidikovna", "position": "Editor", "email": "philolmuz@uzswlu.uz", "phone": "+99891 5080550"}, {"name": "Azizov Solijon Uchmas ugli", "position": "Editor", "email": "", "phone": "+99893 3924778"}]',
    EXTRACT(EPOCH FROM NOW())::bigint
)
ON CONFLICT (k) DO NOTHING;

INSERT INTO settings (k, v, created_at)
VALUES (
    'contact_telegram',
    '@filologiyamasalalari',
    EXTRACT(EPOCH FROM NOW())::bigint
)
ON CONFLICT (k) DO NOTHING;
