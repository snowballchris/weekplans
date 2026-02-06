#!/usr/bin/env sh
set -e

: "${APP_PORT:=5001}"
: "${GUNICORN_WORKERS:=2}"

gunicorn -w "$GUNICORN_WORKERS" -b "127.0.0.1:${APP_PORT}" app:app &

exec nginx -g "daemon off;"
