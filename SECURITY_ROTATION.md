# Security Rotation Checklist

This project previously exposed sensitive data in `db_backup.sql`.  
Use this checklist after history cleanup.

## 1) Git History Cleanup

- Untrack backup file from repository:
  - `git rm --cached db_backup.sql`
- Rewrite history to remove the file from all commits.
- Force-push rewritten history to remote.
- Ask all collaborators to re-clone or hard-reset to the new history.

## 2) Application Secrets

- Rotate local env secrets:
  - `./scripts/security/rotate_local_env_secrets.sh .env`
- Rotate production secrets in deployment environment (not only in repo files):
  - `SECRET_KEY`
  - `FMADMIN_SECRET_KEY`
  - `TRANSLATION_SYNC_TOKEN`
  - `GOOGLE_CLIENT_SECRET`
  - `MAIL_PASSWORD`
  - `DB_PASSWORD`

## 3) Database / User Credential Response

- Force password reset campaign for affected users.
- Invalidate sessions by rotating Flask secret keys.
- Rotate database user password and update deployment secret store.
- Rotate OAuth and SMTP provider credentials from provider dashboards.

## 4) Validation

- Verify `db_backup.sql` is absent from history:
  - `git rev-list --objects --all | grep db_backup.sql` (should return nothing)
- Run tests:
  - `.venv-test/bin/python -m pytest -q`
