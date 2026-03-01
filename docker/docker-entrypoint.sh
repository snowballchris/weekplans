#!/usr/bin/env sh
set -e

: "${APP_PORT:=5001}"
: "${GUNICORN_WORKERS:=2}"

# Ensure static JS files are available (Flask serves from DATA_DIR/static)
mkdir -p /data/static/js
if [ -d /app/static/js ]; then
  cp -f /app/static/js/*.js /data/static/js/ 2>/dev/null || true
fi

gunicorn -w "$GUNICORN_WORKERS" -b "127.0.0.1:${APP_PORT}" app:app &

exec nginx -g "daemon off;"
