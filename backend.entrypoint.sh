#!/bin/sh

set -e

# Wait for PostgreSQL only when using Docker (individual DB vars, not DATABASE_URL)
if [ -z "$DATABASE_URL" ] && [ -n "$DB_HOST" ]; then
  echo "Warte auf PostgreSQL auf $DB_HOST:$DB_PORT..."
  while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
    echo "PostgreSQL ist nicht erreichbar - schlafe 1 Sekunde"
    sleep 1
  done
  echo "PostgreSQL ist bereit - fahre fort..."
fi

python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate

# Create a superuser using environment variables
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created.")
else:
    print(f"Superuser '{username}' already exists.")
EOF

# Seed demo videos from Pexels (skips if videos already exist)
python manage.py seed_demos

# Start RQ worker in background (handles video conversion + email sending)
python manage.py rqworker default &

PORT="${PORT:-8000}"
exec gunicorn core.wsgi:application --bind "0.0.0.0:$PORT"
