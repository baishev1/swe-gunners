#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/swe-gunners/backups}"
KEEP="${KEEP:-14}"
CONTAINER="${CONTAINER:-biletflow-postgres-1}"

mkdir -p "$BACKUP_DIR"
file="$BACKUP_DIR/biletflow-$(date -u +%Y%m%d-%H%M%S).sql.gz"
trap 'rm -f "$file.tmp"' EXIT

docker exec "$CONTAINER" sh -c 'pg_dump -U "$POSTGRES_USER" --clean --if-exists "$POSTGRES_DB"' \
  | gzip > "$file.tmp"
mv "$file.tmp" "$file"

ls -1t "$BACKUP_DIR"/biletflow-*.sql.gz | tail -n +$((KEEP + 1)) | xargs -r rm --

echo "==> Backup written to $file"
