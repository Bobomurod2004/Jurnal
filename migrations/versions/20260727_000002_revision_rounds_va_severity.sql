-- Migration: 20260727_000002_revision_rounds_va_severity
-- Created: 2026-07-27
-- Description: Revizor jarayonidagi "har qanday qaytarish = to'liq qayta
-- taqriz" muammosini hal qilish uchun ikkita qo'shimcha:
--
-- (1) submissions.revision_severity -- 'revision_required'ga kirishda
-- tanlangan daraja ('minor'/'major'). mainweb tomonidagi
-- _compute_revision_reentry mualif qayta yuklaganda shunga qarab qaror
-- qiladi: 'minor' -- tahrirchilar qayta faollashtirilmaydi (to'g'ridan-to'g'ri
-- o'sha admin/muharrir ko'rib chiqadi), 'major' -- to'liq qayta taqriz sikli
-- (mavjud xatti-harakat).
--
-- (2) submission_revision_rounds -- har bir "qaytarish" alohida tarix
-- yozuvi sifatida saqlanadi (round_number, sabab, muharrir fayli, hal
-- qilingan vaqti). Bitta o'zgaruvchan maydon o'rniga tarix bo'lgani uchun
-- mualif dashboardidagi "muharrir fayli" bloki endi hech qachon eskirib,
-- keyingi bosqichlarga aralashib qolmaydi.

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS revision_severity text NOT NULL DEFAULT 'major';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_submissions_revision_severity'
    ) THEN
        ALTER TABLE submissions
            ADD CONSTRAINT chk_submissions_revision_severity
            CHECK (revision_severity IN ('minor', 'major'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS submission_revision_rounds (
    id SERIAL PRIMARY KEY,
    submission_id integer NOT NULL,
    round_number integer NOT NULL,
    severity text NOT NULL DEFAULT 'major',
    editor_assignment_id integer,
    opened_by integer,
    opened_at bigint NOT NULL,
    reason text,
    editor_file text,
    resolved_at bigint,
    created_at bigint NOT NULL DEFAULT EXTRACT(epoch FROM now())
);
CREATE INDEX IF NOT EXISTS idx_submission_revision_rounds_submission
    ON submission_revision_rounds(submission_id, round_number);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_revision_rounds_submission') THEN
        ALTER TABLE submission_revision_rounds
            ADD CONSTRAINT fk_submission_revision_rounds_submission
            FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_revision_rounds_assignment') THEN
        ALTER TABLE submission_revision_rounds
            ADD CONSTRAINT fk_submission_revision_rounds_assignment
            FOREIGN KEY (editor_assignment_id) REFERENCES editor_assignments(id) ON DELETE SET NULL NOT VALID;
    END IF;
END $$;
