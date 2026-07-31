-- Migration: 20260727_000001_antiplagiat_admin_upload_va_chat_attachments
-- Created: 2026-07-27
-- Description: Antiplagiat workflow bo'yicha ikkita yangi imkoniyat:
-- (1) admin ham (mualif o'rniga) antiplagiat faylini yuklay oladi -- kim
--     yuklaganini va tekshiruv natijasini (pending/passed/failed) alohida
--     saqlaymiz, shu bilan "fayl bor" va "fayl tekshiruvdan o'tdi" endi ikki
--     xil narsa; (2) muharrir fayli admin orqali mualifga yuborilganda,
--     mainweb hech qachon editor_assignments jadvalini o'qimagani uchun,
--     shu faylni submissions darajasida nusxalab saqlaymiz.
--
-- Shuningdek submission_messages (mavjud chat) ga fayl/rasm biriktirma
-- ustunlari qo'shiladi (Telegram-simon fayl yuborish).

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS anti_plagiarism_uploaded_by_role text,
    ADD COLUMN IF NOT EXISTS anti_plagiarism_status text NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS anti_plagiarism_note text,
    ADD COLUMN IF NOT EXISTS anti_plagiarism_resubmitted_at bigint,
    ADD COLUMN IF NOT EXISTS editor_shared_file text,
    ADD COLUMN IF NOT EXISTS editor_shared_file_note text,
    ADD COLUMN IF NOT EXISTS editor_shared_file_at bigint;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_submissions_anti_plagiarism_status'
    ) THEN
        ALTER TABLE submissions
            ADD CONSTRAINT chk_submissions_anti_plagiarism_status
            CHECK (anti_plagiarism_status IN ('pending', 'passed', 'failed'));
    END IF;
END $$;

-- Existing rows that already have a checked file were, under the old
-- all-or-nothing gate, implicitly treated as "good enough to proceed" --
-- backfill them as 'passed' so editor assignment gating doesn't regress for
-- submissions already past this stage.
UPDATE submissions
SET anti_plagiarism_status = 'passed'
WHERE anti_plagiarism_status = 'pending'
  AND COALESCE(anti_plagiarism_file, '') != '';

ALTER TABLE submission_messages
    ADD COLUMN IF NOT EXISTS attachment_file text,
    ADD COLUMN IF NOT EXISTS attachment_name text,
    ADD COLUMN IF NOT EXISTS attachment_mime text,
    ADD COLUMN IF NOT EXISTS attachment_size bigint;
