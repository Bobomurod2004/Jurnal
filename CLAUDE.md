# CLAUDE.md — Ilmiy Jurnal Boshqaruv Tizimi (Philology Matters)

## Loyiha haqida

Ilmiy jurnal boshqaruv tizimi — maqolalar qabul qilish, tahrir jarayoni (peer review), nashriyot va to'lov tizimini o'z ichiga olgan platforma. Ikki alohida Flask ilovadan iborat.

## Arxitektura

```
website/
├── mainweb/            # Ommaviy sayt (Flask, port 5000)
│   ├── routes/         # public.py, auth.py, dashboard.py, api.py, context.py
│   ├── modules/        # connector.py (DB), translations.py, fallback_translations.py
│   ├── templates/      # Jinja2 (components/, mainweb/, dashboard/, auth/)
│   ├── src/styles.css  # Tailwind manbasi
│   └── static/styles.css  # Kompilyatsiya qilingan CSS (build natijasi)
├── fmadmin/            # Admin panel (Flask, port 5001)
│   ├── routes/         # web.py (~10k qator, asosiy), api.py
│   ├── connector.py    # O'z DB connector nusxasi
│   └── templates/      # Tabler UI asosida
├── shared/             # publication_metadata.py, database/
├── migrations/         # migrate.py (custom runner) + versions/*.sql
├── tests/              # pytest (DB talab qilmaydi — mock/monkeypatch)
├── scripts/            # init-db.sh, backup.sh, security/
├── nginx/              # Reverse proxy config
├── monitoring/         # Grafana/Loki/Promtail (optional)
├── db_schema.sql       # Boshlang'ich sxema (reference — yangi ustunlar migratsiyalarda!)
└── docker-compose.yml  # + docker-compose.local.yml (dev)
```

## Tech Stack

| Komponent | Texnologiya |
|-----------|------------|
| Backend | Python 3.11+, Flask (blueprint'siz — funksiya nomi `app__route_name` konventsiyasi) |
| Database | PostgreSQL 17, **custom psycopg2 connector** (SQLAlchemy EMAS) |
| Migratsiyalar | Raw SQL fayllar + custom runner (`migrations/migrate.py`) |
| Frontend CSS | Tailwind CSS 4 (postcss build) + tailwindcss-animated + tailwindcss-intersect |
| Ikonkalar | iconify-icon (tabler:*), flag-icons |
| Admin UI | Tabler + Tom Select + Vanilla JS |
| Server | Gunicorn, Nginx, Docker Compose |
| Dev Email | Mailpit |
| API Docs | Flasgger (Swagger) — faqat development |

## DB bilan ishlash (MUHIM)

ORM yo'q — o'ziga xos query-builder ishlatiladi:

```python
# mainweb: extensions.py dagi `dbc` (modules/connector.py — PostgreSQLConnector)
rows = dbc.users.get(id=5).exec()                  # SELECT ... WHERE id=5
rows = dbc.editorial_members.all().exec()          # SELECT *
dbc.users.get(id=5).update(name='X').exec()        # UPDATE
dbc.issues.get().order_by('year').per_page(40).page(1).exec()

# fmadmin: extensions.py dagi `db` (fmadmin/connector.py — alohida nusxa)
```

- Jadval/ustunlar startup'da DB dan avtomatik aniqlanadi. Yangi jadval/ustun qo'shilsa, connector qayta init bo'lishi kerak (server restart yoki `dbc._init_tables()` / `_init_columns()`).
- Murakkab querylar uchun raw SQL ham ishlatiladi.

### Migratsiyalar

- Fayl: `migrations/versions/YYYYMMDD_NNNNNN_tavsif.sql` (raw SQL, **idempotent** yozing — `IF NOT EXISTS`)
- Qo'llash: `python3 migrations/migrate.py migrate` (qo'llanganlar tracking jadvalida saqlanadi)
- Docker'da `db-init` servisi (`scripts/init-db.sh`) avtomatik qo'llaydi
- `db_schema.sql` — faqat boshlang'ich sxema; yangi ustunlar uchun migratsiyalarga qarang

### DB konventsiyalari

- Timestamps: Unix epoch `bigint` (`created_at`, `updated_at`)
- Arrays: PostgreSQL `text[]` (roles, permissions, tags)
- Ko'p til: asosiy ustun (EN) + `_uz`, `_ru` suffiksli ustunlar (masalan `full_name`, `full_name_uz`, `full_name_ru`)
- Soft delete: ba'zi jadvallar `is_deleted` / `is_active` ishlatadi

## Tailwind CSS build (MUHIM!)

```bash
cd mainweb
npm run build:css     # postcss src/styles.css -o static/styles.css
npm run watch:css     # dev rejimda kuzatish
```

**Shablonlarga yangi Tailwind klass qo'shilsa, CSS albatta qayta build qilinishi SHART** — aks holda klasslar ishlamaydi va layout buziladi. Custom komponent stillari ham `mainweb/src/styles.css` da.

## Ko'p tillilik (UZ/RU/EN)

1. **`t('key')`** — Jinja'da asosiy usul; `translations` jadvalidan, topilmasa `mainweb/modules/fallback_translations.py` dagi `EXTRA_STATIC_TRANSLATIONS` dan olinadi.
2. **DB kontenti** — `_localized_content_field()` / `_apply_localized_content()` yordamida `_uz`/`_ru` ustunlardan tanlanadi.
3. **Route-darajadagi UI lug'atlar** — ba'zi sahifalar o'z dict'lariga ega (masalan `EDITORIAL_UI_TEXTS`, `ISSUE_UI_TEXTS` — `mainweb/routes/public.py`).
4. Joriy til: `session['language']` (`_current_lang_code()` — uz/ru/en, default en).

Yangi UI matn qo'shganda hardcode qilmang — yuqoridagi usullardan biriga qo'shing.

## Autentifikatsiya

1. **Email/Parol** — 6 raqamli kod (TTL 900s), rate limit 5 urinish / 15 daqiqa
2. **Google OAuth** (`GOOGLE_AUTH_ENABLED`), **ORCID OAuth** (`ORCID_AUTH_ENABLED`, sandbox/production)
3. Session: cookie-based, 24 soat, HttpOnly + SameSite=Lax; parollar Werkzeug hash

### Rollar (RBAC)
`superadmin` → `admin` → `editor` → `author`. Foydalanuvchi imkoniyatlari `tariffs.permissions` array'iga ham bog'liq.

## Tahrir hay'ati (editorial_members)

- Jadval: `editorial_members` (migratsiyalarda yaratilgan; profil maydonlari: `country*`, `country_code`, `research_interests*`, `scopus_author_id/url`, `researcherid/url`, `orcid`, `cv_file*`, `google_scholar_url`)
- A'zo turlari (yangi tizim): `editor_in_chief`, `deputy_editor_in_chief`, `executive_secretary`, `editorial_board`, `international_editorial_board`, `editorial_council`, `international_editorial_council`
- Eski turlar (`deputy_editor`, `reviewer`, ...) `EDITORIAL_MEMBER_TYPE_LEGACY_ALIASES` orqali yangilariga map qilinadi
- Ommaviy sahifa: `/editorial` — rahbariyat (featured guruhlar) turg'un kartalar, qolgan guruhlar harakatlanuvchi (marquee) lentada; har guruhning rang temasi `EDITORIAL_GROUP_THEMES` da
- Admin: fmadmin → `templates/website/editorial/`

## Submission workflow (fmadmin)

Texnik tekshiruv → Anti-plagiat → Peer review → Muharrir ko'rib chiqish → To'lov → Nashr.
**Holatlar qat'iy tartibda o'zgaradi — bu tartibni buzmang.**

## Local Development

```bash
# Docker bilan
docker compose -f docker-compose.local.yml up --build
# Sayt: http://localhost:8080/  Admin: http://localhost:8080/fmadmin/
# Mailpit: http://localhost:8025/  DB: localhost:5434

# To'g'ridan-to'g'ri (venv bilan)
python mainweb/run.py    # :5000
python fmadmin/run.py    # :5001
```

## Testing

```bash
.venv-test/bin/pytest tests/    # yoki: pytest tests/
```

- Testlar DB'siz ishlaydi (monkeypatch/mock)
- Request-context kerak bo'lsa: `app.test_request_context()` ishlatiladi
- Fayllar: `test_regressions.py`, `test_security_regressions.py`, `test_utils.py`

## DB boshqarish

```bash
docker compose exec db pg_dump -U postgres journal2 > backup_$(date +%Y%m%d).sql   # backup
docker compose exec -T db psql -U postgres journal2 < backup.sql                  # restore
docker compose exec db psql -U postgres journal2                                  # konsol
python3 migrations/migrate.py migrate                                             # migratsiya
```

## Production Deploy

```bash
docker compose up -d --build db db-init mainweb fmadmin   # host nginx bilan (tavsiya)
docker compose --profile docker-nginx up -d --build       # docker nginx bilan
```

## Environment Variables (`.env`)

```bash
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
FLASK_ENV=development|production
APP_HOST, APP_BASE_URL
SECRET_KEY=<32+ belgi>          FMADMIN_SECRET_KEY=<32+ belgi>
GOOGLE_AUTH_ENABLED=false       ORCID_AUTH_ENABLED=false
ORCID_BASE_URL=https://sandbox.orcid.org   # yoki https://orcid.org
MAIL_ENABLED, MAIL_HOST, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
AUTH_EMAIL_CODE_TTL_SECONDS=900 AUTH_EMAIL_CODE_MAX_ATTEMPTS=5
SAVE_PATH=/var/www/journal/     # fayl yuklamalar
```

## Muhim qoidalar (Claude uchun)

1. **Til**: kod va kommentariyalar inglizcha; UI matnlar 3 tilda (yuqoridagi tarjima tizimi orqali, hardcode emas).
2. **Xavfsizlik**: SQL injection, XSS, CSRF dan saqlaning; input validation server-side; fmadmin'da har doim admin autentifikatsiyasi tekshirilsin.
3. **CSS**: shablon o'zgarsa → `npm run build:css` (mainweb'da) — unutmang!
4. **Migratsiya**: yangi ustun/jadval — faqat `migrations/versions/` da yangi SQL fayl (idempotent), `db_schema.sql` ni ham yangilab qo'yish ma'qul.
5. **Fayl yuklash**: fayllar `SAVE_PATH` ga, yo'llar DB ga.
6. **Email**: faqat shared mail util orqali; `MAIL_ENABLED=false` da yuborilmaydi.
7. **Workflow**: submission holatlari tartibini buzmang.
8. **Testlar**: o'zgarishdan keyin `pytest tests/` ishga tushiring; route helper funksiyalari uchun regression test qo'shish odat qilingan.

## Xavfsizlik ogohlantirishlari

- `.env` da production credentials bor — git'ga tushmasin
- `SECRET_KEY` ≠ `FMADMIN_SECRET_KEY` ≠ `TRANSLATION_SYNC_TOKEN`, har biri 32+ belgi
- `/fmadmin/` tashqi internetdan bevosita ochiq bo'lmasligi kerak
