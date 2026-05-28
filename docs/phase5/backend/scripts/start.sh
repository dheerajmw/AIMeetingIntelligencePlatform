#!/bin/sh
set -e

PORT="${PORT:-8002}"
STORAGE="${STORAGE_ROOT:-/app/storage}"

mkdir -p "${STORAGE}/uploads" "${STORAGE}/samples" "${STORAGE}/meetings"

# Render persistent disk (optional): mount at /var/data and set STORAGE_ROOT + DATABASE_URL in the dashboard.
if [ -d /var/data ]; then
  mkdir -p /var/data/storage /var/data/storage/uploads
fi

DB_DIR="$(dirname "${DATABASE_URL#sqlite:///}")"
if [ -n "${DB_DIR}" ] && [ "${DB_DIR}" != "." ]; then
  mkdir -p "${DB_DIR}"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
