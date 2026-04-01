#!/usr/bin/env bash
# Database initialization script
# Ensures schema, migrations, and baseline seed data are in place.

set -euo pipefail

echo "=========================================="
echo "Database Initialization Script"
echo "=========================================="

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-journal2}"

if [ -z "${PGPASSWORD:-}" ] && [ -n "${DB_PASSWORD}" ]; then
  export PGPASSWORD="${DB_PASSWORD}"
fi

psql_cmd() {
  psql -w -v ON_ERROR_STOP=1 -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "$@"
}

createdb_cmd() {
  createdb -w -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "$@"
}

if ! command -v pg_isready >/dev/null 2>&1; then
  echo "Error: pg_isready is not installed in this container."
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "Error: psql is not installed in this container."
  exit 1
fi

echo "Target database: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "Waiting for database..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

echo "Checking database..."
if ! psql_cmd -lqt | cut -d \| -f 1 | grep -qw "${DB_NAME}"; then
    echo "Creating database ${DB_NAME}..."
    createdb_cmd "${DB_NAME}"
    echo "Database created!"
else
    echo "Database ${DB_NAME} already exists"
fi

echo "Checking schema..."
TABLE_COUNT=$(psql_cmd -d "${DB_NAME}" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")

if [ "${TABLE_COUNT}" -eq "0" ]; then
    echo "No tables found. Applying initial schema..."
    if [ -f "/docker-entrypoint-initdb.d/01-schema.sql" ]; then
        psql_cmd -d "${DB_NAME}" -f "/docker-entrypoint-initdb.d/01-schema.sql"
        echo "Schema applied!"
    else
        echo "Warning: /docker-entrypoint-initdb.d/01-schema.sql not found"
    fi
else
    echo "Schema already exists (${TABLE_COUNT} tables)"
fi

TRANSLATIONS_TABLE_EXISTS=$(psql_cmd -d "${DB_NAME}" -tAc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='translations');")
if [ "${TRANSLATIONS_TABLE_EXISTS}" = "t" ]; then
    TRANSLATIONS_COUNT=$(psql_cmd -d "${DB_NAME}" -tAc "SELECT COUNT(*) FROM translations;")
else
    TRANSLATIONS_COUNT=0
fi

if [ "${TRANSLATIONS_COUNT}" -eq "0" ] && [ -f "/docker-entrypoint-initdb.d/02-translations.sql" ]; then
    echo "Applying translations seed..."
    psql_cmd -d "${DB_NAME}" -f "/docker-entrypoint-initdb.d/02-translations.sql"
    echo "Translations seed applied!"
fi

echo "Applying migrations..."
cd /app
python3 migrations/migrate.py migrate

echo "Seeding baseline data..."
python3 mainweb/scripts/seed_baseline_data.py

if [ -n "${SUPERADMIN_EMAIL:-}" ] && [ -n "${SUPERADMIN_PASSWORD:-}" ]; then
    echo "Ensuring fmadmin superadmin account exists..."
    python3 fmadmin/create_superadmin.py \
      --email "${SUPERADMIN_EMAIL}" \
      --name "${SUPERADMIN_NAME:-Super Admin}" \
      --password "${SUPERADMIN_PASSWORD}"
else
    echo "SUPERADMIN_EMAIL/SUPERADMIN_PASSWORD are not set. Skipping superadmin bootstrap."
fi

echo "=========================================="
echo "Database initialization complete!"
echo "=========================================="
