#!/bin/sh
set -e

echo "⏳ Waiting for Postgres..."
until nc -z "$DATABASE_HOST" "$DATABASE_PORT"; do
  sleep 1
done

echo "✅ Postgres is up - running migrations"
alembic upgrade head

echo "🚀 Starting app"

gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app