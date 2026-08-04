-- Migration: 20260804_000002_fix_promoted_editor_primary_role
-- Created: 2026-08-04
-- Description: Saytda ro'yxatdan o'tgan foydalanuvchi keyinchalik muharrir
-- qilinganda (fmadmin -> Tahrirchilar -> tahrirlash) faqat `roles` massiviga
-- 'editor' qo'shilardi, `rolename` esa 'user' bo'lib qolaverardi. fmadmin
-- interfeysi va tekshiruv oqimi esa aynan birlamchi rol (primary_role ->
-- rolename) bo'yicha qaror qiladi. Natijada bunday muharrir:
--   * topshiriqni ochsa ham u "qabul qilindi" deb belgilanmasdi
--     (accepted_at NULL) va qabul muddati o'tgach avtomatik olib tashlanardi;
--   * tahriz yuborish formasini umuman ko'rmasdi;
--   * "Tayinlovlar" ro'yxatida o'zining emas, hamma muharrirlarning
--     topshiriqlarini ko'rardi.
--
-- Kod tomoni tuzatildi (endi rol massivi + editor_id bo'yicha qaror
-- qilinadi), bu yerda esa mavjud hisoblarning ma'lumoti tenglashtiriladi.
-- Hech qanday yangi huquq berilmaydi: bu hisoblar 'editor' rolini va uning
-- ruxsatlarini allaqachon olgan; faqat birlamchi rol nomi to'g'rilanadi.
-- Admin/superadmin birlamchi roli o'zgarmaydi (ular yuqoriroq).
-- `roles` massivi tegilmaydi, ya'ni muallif sifatidagi kirish saqlanadi.

UPDATE users
SET rolename = 'editor'
WHERE roles IS NOT NULL
  AND 'editor' = ANY(roles)
  AND COALESCE(LOWER(TRIM(rolename)), '') NOT IN ('editor', 'admin', 'superadmin');
