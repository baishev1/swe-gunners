#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/swe-gunners/app}"
ENV_FILE="${ENV_FILE:-/opt/swe-gunners/.env}"

cd "$APP_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "error: missing environment file at $ENV_FILE" >&2
  exit 1
fi

export APP_ENV_FILE="$ENV_FILE"
COMPOSE=(docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml)

echo "==> Building images"
"${COMPOSE[@]}" build --pull

echo "==> Starting database"
"${COMPOSE[@]}" up -d postgres

echo "==> Applying migrations"
"${COMPOSE[@]}" run --rm -T backend alembic upgrade head

echo "==> Starting services"
"${COMPOSE[@]}" up -d --remove-orphans --wait

echo "==> Removing dangling images"
docker image prune -f >/dev/null

echo "==> Trimming build cache"
docker builder prune -f --reserved-space 1GB --min-free-space 2GB >/dev/null

echo "==> Verifying HTTP endpoint"
curl --fail --silent --show-error --retry 10 --retry-delay 2 \
  http://127.0.0.1:8080/health >/dev/null

echo "==> Deployed $(date -u +%Y-%m-%dT%H:%M:%SZ)"
