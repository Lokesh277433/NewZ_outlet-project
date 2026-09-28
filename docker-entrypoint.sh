#!/bin/sh
set -e

mkdir -p "${DATA_DIR:-/app/data}/media"

python manage.py migrate --noinput
python manage.py setup_groups
python manage.py collectstatic --noinput

if [ "${SEED_DATA:-0}" = "1" ]; then
  python manage.py seed_data
fi

exec gunicorn News_outlet.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
