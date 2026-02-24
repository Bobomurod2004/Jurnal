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

### Запуск

```bash
# 1. Клонировать или перейти в директорию проекта
cd /path/to/website

# 2. Запустить все сервисы
docker-compose up -d

# 3. Проверить статус
docker-compose ps
```

### Доступ

| Сервис | URL |
|--------|-----|
| Основной сайт | http://localhost/ |
| Админ-панель | http://localhost/fmadmin/ |

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
