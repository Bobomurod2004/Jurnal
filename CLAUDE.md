# CLAUDE.md — Ilmiy Jurnal Boshqaruv Tizimi

## Loyiha haqida

Bu **ilmiy jurnal boshqaruv tizimi** — maqolalar qabul qilish, tahrir jarayoni, nashriyot va to'lov tizimini o'z ichiga olgan to'liq platforma. Ikki alohida Flask ilovadan iborat.

## Arxitektura

```
website/
├── mainweb/          # Asosiy sayt (Flask, port 5000) — ommaviy
├── fmadmin/          # Admin panel (Flask, port 5001) — ichki
├── shared/           # Umumiy modullar (DB, email, utils)
├── migrations/       # Alembic migratsiyalar
├── nginx/            # Reverse proxy konfiguratsiya
├── scripts/          # Deploy va init skriptlar
├── tests/            # pytest test to'plami
├── monitoring/       # Grafana/Loki/Promtail
├── db_schema.sql     # To'liq DB sxemasi
└── docker-compose.yml
```

## Tech Stack

| Komponent | Texnologiya |
|-----------|------------|
| Backend | Python 3.11, Flask |
| ORM | Flask-SQLAlchemy, Flask-Migrate (Alembic) |
| Database | PostgreSQL 17 |
| Frontend CSS | Tailwind CSS 4.0 + tailwindcss-animated + tailwindcss-intersect |
| Admin UI | Tabler + Tom Select + Vanilla JS |
| Template | Jinja2 |
| Server | Gunicorn (4 workers, 1 thread, 120s timeout) |
| Proxy | Nginx Alpine |
| Container | Docker + Docker Compose |
| Logging | Loki + Promtail + Grafana (optional) |
| Dev Email | Mailpit |
| API Docs | Flasgger (Swagger) — faqat developmentda |

## Loyiha kodlash qoidalari

### Til
- **Kod va kommentariyalar**: inglizcha
- **UI matnlar**: ko'p til (UZ/RU/EN) — `translations` jadvalidan olinadi
- **DB ustunlar multi-til**: `title_uz`, `title_ru`, `title_en` formati

### Python
- Flask blueprintlar ishlatiladi — har bir modul o'z blueprint'iga ega
- `shared/` papkasidagi modullar ikkala ilovada ham ishlatiladi
- Settings `.env` faylidan `python-dotenv` orqali yuklanadi
- Parollar Werkzeug `generate_password_hash` / `check_password_hash` bilan
- Barcha DB operatsiyalari SQLAlchemy orqali (raw SQL faqat murakkab querylarda)

### DB konventsiyalari
- Timestamps: Unix epoch `bigint` (`created_at`, `updated_at`)
- Arrays: PostgreSQL `text[]` (roles, permissions, tags)
- Multi-til: alohida ustunlar (`_uz`, `_ru`, `_en` suffiks)
- Soft delete: ba'zi jadvallar `is_deleted` field ishlatadi

### Frontend
- Tailwind utility classlar — custom CSS minimal
- JavaScript faqat vanilla (admin panelda)
- Mainwebda form validation server-side

## Authentication tizimi

1. **Email/Parol** — asosiy usul
   - 6 raqamli verifikatsiya kodi (TTL: 900s)
   - Rate limiting: 5 urinish / 15 daqiqa
   - Parol recovery email orqali
2. **Google OAuth** — optional (`GOOGLE_AUTH_ENABLED`)
3. **ORCID OAuth** — optional (`ORCID_AUTH_ENABLED`), sandbox/production
4. **Session**: Cookie-based, 24 soat, HttpOnly + SameSite=Lax

### Rollar (RBAC)
- `superadmin` — to'liq access
- `admin` — boshqaruv
- `editor` — tahrir jarayoni
- `author` — maqola yuborish

## Asosiy xususiyatlar

### Mainweb (ommaviy sayt)
- Maqolalar ro'yxati va ko'rish
- Sonlar (issues) ko'rish
- Yangiliklar
- Muharrir hay'ati
- Dinamik sahifalar (CMS) — `/<alias>` yo'li
- Foydalanuvchi dashboard:
  - Profil (ORCID integratsiya)
  - Maqola yuborish va holat kuzatish
  - To'lov tarixi
  - Yuklamalar tarixi

### fmadmin (admin panel)
- Submission workflow:
  1. Texnik tekshiruv
  2. Anti-plagiat
  3. Peer review tayinlash
  4. Muharrir ko'rib chiqish
  5. To'lov
  6. Nashr
- Foydalanuvchilar boshqaruvi
- Nashrlar tahrirlash (ko'p tilda)
- To'lov va tarif boshqaruvi
- Statistika dashboard

## Muhim fayllar

| Fayl | Vazifasi |
|------|---------|
| `mainweb/settings.py` | Mainweb konfiguratsiya |
| `fmadmin/settings.py` | fmadmin konfiguratsiya |
| `shared/db.py` | SQLAlchemy instance |
| `shared/mail.py` | Email yuborish |
| `shared/models/` | DB modellari |
| `db_schema.sql` | To'liq DB sxemasi (reference) |
| `migrations/versions/` | Alembic migratsiya fayllari |
| `scripts/init-db.sh` | DB initsializatsiya skripti |

## Environment Variables (`.env`)

```bash
# DB
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# App
FLASK_ENV=development|production
APP_HOST=domain.com
APP_BASE_URL=https://domain.com
SECRET_KEY=<32+ char>
FMADMIN_SECRET_KEY=<32+ char>

# OAuth (optional)
GOOGLE_AUTH_ENABLED=false
ORCID_AUTH_ENABLED=false
ORCID_BASE_URL=https://sandbox.orcid.org  # yoki https://orcid.org

# Email
MAIL_ENABLED=true
MAIL_HOST, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD

# Auth codes
AUTH_EMAIL_CODE_TTL_SECONDS=900
AUTH_EMAIL_CODE_MAX_ATTEMPTS=5

# Uploads
SAVE_PATH=/var/www/journal/
```

## Local Development

```bash
# Docker bilan ishga tushirish
docker compose -f docker-compose.local.yml up --build

# URL lar
# Asosiy sayt:  http://localhost:8080/
# Admin panel:  http://localhost:8080/fmadmin/
# Mailpit:      http://localhost:8025/
# DB:           localhost:5434
```

## Production Deploy

```bash
# Host nginx bilan (tavsiya)
docker compose up -d --build db db-init mainweb fmadmin

# Docker nginx bilan
docker compose --profile docker-nginx up -d --build
```

## Testing

```bash
# Test ishga tushirish
pytest tests/

# Yoki Docker ichida
docker compose exec mainweb pytest /app/tests/
```

## Tailwind CSS build (mainweb)

```bash
cd mainweb
npm install
npm run build  # yoki: npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css
```

## DB boshqarish

```bash
# Backup
docker compose exec db pg_dump -U postgres journal2 > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T db psql -U postgres journal2 < backup.sql

# DB konsol
docker compose exec db psql -U postgres journal2

# Migratsiya qo'shish
flask db migrate -m "description"
flask db upgrade
```

## Muhim qoidalar (Claude uchun)

1. **Xavfsizlik**: SQL injection, XSS, CSRF dan saqlaning. Input validation server-side.
2. **Ko'p til**: Yangi matnlar `translations` jadvaliga qo'shiladi, hardcode qilinmaydi.
3. **Sessiya**: Foydalanuvchi autentifikatsiyasi tekshirilganda `session` dict ishlatiladi.
4. **Fayl yuklash**: Fayllar `SAVE_PATH` ga saqlanadi, yo'llar DB da saqlanadi.
5. **Email**: Barcha email yuborish `shared/mail.py` orqali, `MAIL_ENABLED=false` da yuborilmaydi.
6. **Admin panel**: `fmadmin/` da har doim admin autentifikatsiyasi tekshirilsin.
7. **Tarif tizimi**: Foydalanuvchi imkoniyatlari `tariffs` jadvalidagi `permissions` array ga bog'liq.
8. **Workflow holatlari**: Submission holatlari qat'iy tartibda o'zgaradi — bu tartibni buzmang.

## Xavfsizlik ogohlantirishlari

- `.env` faylida production credentials mavjud — git'ga push qilinmasin
- `SECRET_KEY` va `FMADMIN_SECRET_KEY` production'da 32+ belgi bo'lishi shart
- `TRANSLATION_SYNC_TOKEN` `SECRET_KEY` dan farq qilishi shart
- Admin panel (`/fmadmin/`) tashqi internetdan bevosita accessible bo'lmasligi kerak
