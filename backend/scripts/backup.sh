#!/bin/bash
# SignalFlow AI — Database backup script
# Uploads PostgreSQL dump to S3/R2 for offsite storage
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="signalflow_${TIMESTAMP}.sql.gz"
TMP_PATH="/tmp/${BACKUP_FILE}"

echo "[$(date)] Starting backup..."

# Dump and compress
# Use DATABASE_URL_SYNC (standard postgres:// scheme) since pg_dump doesn't support asyncpg
DB_URL="${DATABASE_URL_SYNC:-${DATABASE_URL}}"
# Strip asyncpg scheme if present (pg_dump needs standard postgres://)
DB_URL="${DB_URL/postgresql+asyncpg/postgresql}"
pg_dump "$DB_URL" | gzip > "${TMP_PATH}"
FILESIZE=$(stat -f%z "${TMP_PATH}" 2>/dev/null || stat -c%s "${TMP_PATH}")
echo "[$(date)] Dump complete: ${FILESIZE} bytes"

# Upload to S3/R2 (requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BACKUP_BUCKET)
if [ -n "${BACKUP_BUCKET:-}" ]; then
    aws s3 cp "${TMP_PATH}" "s3://${BACKUP_BUCKET}/${BACKUP_FILE}"
    echo "[$(date)] Uploaded to s3://${BACKUP_BUCKET}/${BACKUP_FILE}"
else
    echo "[$(date)] WARNING: BACKUP_BUCKET not set, skipping S3 upload"
fi

# Cleanup
rm -f "${TMP_PATH}"
echo "[$(date)] Backup complete: ${BACKUP_FILE}"
