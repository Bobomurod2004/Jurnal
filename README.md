# Journal Website - Dockerized Deployment

Система управления научным журналом с двумя Flask-приложениями: основной сайт и админ-панель.

## 📁 Структура проекта

```
website/
├── mainweb/           # Основной сайт (Flask + Tailwind)
├── fmadmin/           # Админ-панель (Flask)
├── static/            # Общие статические файлы
├── nginx/             # Конфигурация Nginx
├── db_backup.sql      # Резервная копия БД
├── docker-compose.yml # Оркестрация контейнеров
├── Dockerfile         # Образ для Flask-приложений
└── requirements.txt   # Python зависимости
```

## 🚀 Быстрый старт

### Требования
- Docker Desktop >= 4.0
- Docker Compose >= 2.0

### Production запуск

```bash
# 1. Клонировать или перейти в директорию проекта
cd /path/to/website

# 2. Запустить production-сервисы
docker-compose up -d

# 3. Проверить статус
docker-compose ps
```

### Local запуск

```bash
# 1. Перейти в директорию проекта
cd /path/to/website

# 2. Запустить local development окружение
docker compose -f docker-compose.local.yml up --build
```

Local URLs:

| Сервис | URL |
|--------|-----|
| Main site via local nginx | http://localhost:8080/ |
| Admin via local nginx | http://localhost:8080/fmadmin/ |
| Main site direct | http://localhost:5000/ |
| Admin direct | http://localhost:5001/fmadmin/ |
| Mailpit inbox | http://localhost:8025/ |
| PostgreSQL | localhost:5434 |

### Доступ

| Сервис | URL |
|--------|-----|
| Основной сайт | https://your-domain/ |
| Админ-панель | https://your-domain/fmadmin/ |

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────┐
│                    Nginx (:80)                      │
│  ┌──────────────────┬─────────────────────────────┐ │
│  │  /               │  /fmadmin/                  │ │
└──┼──────────────────┼─────────────────────────────┼─┘
   │                  │                             │
   ▼                  ▼                             │
┌─────────┐    ┌─────────┐                          │
│ mainweb │    │ fmadmin │                          │
│  :5000  │    │  :5001  │                          │
└────┬────┘    └────┬────┘                          │
     │              │                               │
     └──────┬───────┘                               │
            ▼                                       │
     ┌────────────┐                                 │
     │ PostgreSQL │◄────────────────────────────────┘
     │   :5432    │     (static files)
     └────────────┘
```

## ⚙️ Конфигурация

### Переменные окружения

Файл `.env` в корне проекта:

```env
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=journal2
APP_HOST=your-domain
APP_BASE_URL=https://your-domain
APP_VERSION=1.0.0
LOG_LEVEL=INFO
SECRET_KEY=change-this-mainweb-secret
FMADMIN_SECRET_KEY=change-this-fmadmin-secret
TRANSLATION_SYNC_TOKEN=change-this-sync-token
MAIL_ENABLED=1
MAIL_HOST=smtp.your-provider.tld
MAIL_PORT=587
MAIL_USERNAME=philologymatters@uzswlu.uz
MAIL_PASSWORD=your-real-smtp-password
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_FROM_EMAIL=philologymatters@uzswlu.uz
MAIL_FROM_NAME=Philology Matters
MAIL_REPLY_TO=philologymatters@uzswlu.uz
MAIL_CONTACT_RECIPIENTS=philologymatters@uzswlu.uz,philolm.uz@gmail.com
```

### Email note

- Local development: `docker-compose.local.yml` automatically starts Mailpit on `http://localhost:8025/`, and any entered recipient email will be captured there.
- If you put real `MAIL_*` SMTP values into root `.env`, local Docker will use those values instead of Mailpit and emails will go to the real inbox.
- Production: configure a real SMTP account for `philologymatters@uzswlu.uz`. The contact form copies are sent to `philologymatters@uzswlu.uz` and `philolm.uz@gmail.com` by default.
- Before production go-live, you still need SMTP credentials plus DNS records for deliverability: `SPF`, `DKIM`, and preferably `DMARC`.

### Recommended real working production option

If you want the fastest practical setup without waiting for university SMTP access:

1. Copy `[.env.production.example](./.env.production.example)` into your server `.env`.
2. Keep `MAIL_USERNAME=philolm.uz@gmail.com`.
3. In Google account security, generate an App Password for `philolm.uz@gmail.com`.
4. Put that App Password into `MAIL_PASSWORD`.
5. Keep `MAIL_REPLY_TO=philologymatters@uzswlu.uz`.
6. Keep `MAIL_CONTACT_RECIPIENTS=philologymatters@uzswlu.uz,philolm.uz@gmail.com`.

This means:
- emails are actually sent through Gmail SMTP;
- replies go to `philologymatters@uzswlu.uz`;
- contact form copies go to both real inboxes.

## ✅ Versioning (Release)

Recommended release versioning:

1. Use Git tags: `v1.0.0`, `v1.0.1`, `v1.1.0`
2. Put the same value into `APP_VERSION` in `.env` for production.
3. `/healthz` endpoints will return the current version.

Example:

```bash
git tag v1.0.0
APP_VERSION=1.0.0
docker-compose up -d --build
```

Optional: push to a registry by setting `IMAGE_REGISTRY` (must end with `/`):

```env
IMAGE_REGISTRY=registry.example.com/journal/
```

Then build and push:

```bash
APP_VERSION=1.0.0
docker compose build
docker push registry.example.com/journal/journal_mainweb:1.0.0
docker push registry.example.com/journal/journal_fmadmin:1.0.0
```

Rollback example:

```bash
APP_VERSION=0.9.0
docker compose pull
docker compose up -d
```

## 📊 Logging / Grafana (Production)

We provide an optional observability stack with **Grafana + Loki + Promtail**.

Start it together with production services:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d
```

Grafana UI:
- http://your-domain:3000
- user: `${GRAFANA_ADMIN_USER}`
- pass: `${GRAFANA_ADMIN_PASSWORD}`

Logs from `mainweb` and `fmadmin` are shipped to Loki automatically.

### Production email test

After filling production `.env`, you can test the email transport with:

```bash
python mainweb/scripts/send_test_email.py your-email@example.com
```

### Порты

| Сервис | Порт | Описание |
|--------|------|----------|
| Nginx | 80 | HTTP (публичный) |
| PostgreSQL | 5432 | База данных |
| mainweb | 5000 | Flask (внутренний) |
| fmadmin | 5001 | Flask (внутренний) |

## 📦 Управление

### Логи

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f mainweb
docker-compose logs -f fmadmin
docker-compose logs -f db
```

### Перезапуск

```bash
# Перезапустить конкретный сервис
docker-compose restart mainweb

# Перезапустить все
docker-compose restart
```

### Остановка

```bash
# Остановить (сохранить данные)
docker-compose down

# Остановить и удалить данные
docker-compose down -v
```

### Пересборка

```bash
# После изменения кода
docker-compose up -d --build
```

## 🔧 Разработка

Для локальной разработки без Docker:

```bash
# 1. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить .env
# DB_HOST=127.0.0.1
# DB_PORT=5432

# 4. Запустить mainweb
cd mainweb
python run.py

# 5. В другом терминале - fmadmin
cd fmadmin
python run.py
```

Для Docker local используются:

- `docker-compose.local.yml` для development-окружения
- `nginx/nginx.local.conf` для локального reverse proxy без SSL
- `docker-compose.yml` и `nginx/nginx.conf` только для production/server

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## 🗄 База данных

### Резервное копирование

```bash
docker-compose exec db pg_dump -U postgres journal2 > backup_$(date +%Y%m%d).sql
```

### Восстановление

```bash
docker-compose exec -T db psql -U postgres journal2 < backup.sql
```

### Доступ к консоли

```bash
docker-compose exec db psql -U postgres journal2
```

## 🐛 Решение проблем

### Ошибка подключения к БД
```bash
# Проверить статус БД
docker-compose exec db pg_isready -U postgres

# Перезапустить БД
docker-compose restart db
```

### Контейнер не запускается
```bash
# Проверить логи
docker-compose logs <service_name>

# Пересобрать образ
docker-compose build --no-cache <service_name>
```

### Порт 80 занят
```bash
# Изменить порт в docker-compose.yml
ports:
  - "8080:80"  # Использовать http://localhost:8080
```

## 📝 Лицензия

MIT License
