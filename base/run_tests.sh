#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

NET=basenet_$$
PG=basepg_$$
docker network create "$NET" >/dev/null
docker run -d --rm --name "$PG" --network "$NET" \
  -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=appdb \
  postgres:16 >/dev/null

cleanup() { docker rm -f "$PG" >/dev/null 2>&1 || true; docker network rm "$NET" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "waiting for postgres..."
until docker exec "$PG" pg_isready -U app -d appdb >/dev/null 2>&1; do sleep 1; done

docker run --rm --network "$NET" -v "$PWD":/code -w /code \
  -e DATABASE_URL=postgresql+psycopg2://app:app@"$PG":5432/appdb \
  python:3.12-slim bash -c "pip install -q -r requirements.txt && python -m pytest -v"
