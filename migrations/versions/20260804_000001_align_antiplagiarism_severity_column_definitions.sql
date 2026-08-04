-- Migration: 20260804_000001_align_antiplagiarism_severity_column_definitions
-- Created: 2026-08-04
-- Description: 20260727_000001 va 20260727_000002 submissions jadvaliga
-- anti_plagiarism_status va revision_severity ustunlarini NOT NULL DEFAULT
-- bilan qo'shadi. Lekin bu ustunlarni runtime schema-sync (dev qulayligi,
-- SUBMISSION_EXTRA_COLUMN_TYPES) allaqachon yaratib qo'ygan bo'lsa,
-- ADD COLUMN IF NOT EXISTS jimgina o'tib ketadi va ustun kuchsizroq
-- (nullable) ta'rif bilan qoladi. Natijada dev va production sxemasi
-- ajralib ketadi -- 20260721_000003 da revision_number/revision_allowed
-- uchun aynan shu holat hujjatlashtirilgan edi.
--
-- Shuning uchun ta'riflarni har qanday muhitda bir xillashtiramiz.
--
-- Backfill UPDATE'i user_id'si mavjud qatorlar bilan cheklangan: qatorning
-- ISTALGAN ustunini yangilash o'sha qatorning BARCHA cheklovlarini, shu
-- jumladan avvaldan mavjud NOT VALID fk_submissions_user cheklovini ham
-- qayta tekshiradi, bazada esa kamida bitta eski "yetim" submission bor
-- (u bu migratsiyaga aloqador emas, tegmaymiz).
--
-- SET NOT NULL esa DO blok ichida: agar shunday yetim qatorda NULL qolib
-- ketgan bo'lsa, migratsiya deploy'ni to'xtatib qo'ymasligi kerak --
-- DEFAULT baribir o'rnatiladi va ilova kodi ham qiymatni aniq yuboradi.

UPDATE submissions s SET anti_plagiarism_status = 'pending'
WHERE s.anti_plagiarism_status IS NULL
  AND EXISTS (SELECT 1 FROM users u WHERE u.id = s.user_id);

UPDATE submissions s SET revision_severity = 'major'
WHERE s.revision_severity IS NULL
  AND EXISTS (SELECT 1 FROM users u WHERE u.id = s.user_id);

ALTER TABLE submissions ALTER COLUMN anti_plagiarism_status SET DEFAULT 'pending';
ALTER TABLE submissions ALTER COLUMN revision_severity SET DEFAULT 'major';

DO $$
BEGIN
    ALTER TABLE submissions ALTER COLUMN anti_plagiarism_status SET NOT NULL;
EXCEPTION WHEN others THEN
    RAISE NOTICE 'submissions.anti_plagiarism_status stays nullable: %', SQLERRM;
END $$;

DO $$
BEGIN
    ALTER TABLE submissions ALTER COLUMN revision_severity SET NOT NULL;
EXCEPTION WHEN others THEN
    RAISE NOTICE 'submissions.revision_severity stays nullable: %', SQLERRM;
END $$;
