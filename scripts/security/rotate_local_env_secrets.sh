#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required to generate secure random values" >&2
  exit 1
fi

BACKUP_FILE="${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
cp "$ENV_FILE" "$BACKUP_FILE"

replace_or_append() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf "\n%s=%s\n" "$key" "$value" >> "$ENV_FILE"
  fi
}

replace_or_append "SECRET_KEY" "$(openssl rand -hex 32)"
replace_or_append "FMADMIN_SECRET_KEY" "$(openssl rand -hex 32)"
replace_or_append "TRANSLATION_SYNC_TOKEN" "$(openssl rand -hex 24)"

# These secrets must also be rotated on provider side first.
replace_or_append "GOOGLE_CLIENT_SECRET" "ROTATE_IN_GOOGLE_CONSOLE_AND_UPDATE"
replace_or_append "MAIL_PASSWORD" "ROTATE_IN_SMTP_PROVIDER_AND_UPDATE"

echo "Backup created: $BACKUP_FILE"
echo "Rotated in $ENV_FILE: SECRET_KEY, FMADMIN_SECRET_KEY, TRANSLATION_SYNC_TOKEN"
echo "Set placeholders in $ENV_FILE: GOOGLE_CLIENT_SECRET, MAIL_PASSWORD"
