#!/bin/sh
set -e

echo ">>> Waiting for database..."
python << END
import sys
import time
import psycopg2
from psycopg2 import OperationalError

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            dbname="${DB_NAME}",
            user="${DB_USER}",
            password="${DB_PASSWORD}",
            host="${DB_HOST}",
            port="${DB_PORT}"
        )
        conn.close()
        print("Database is ready!")
        sys.exit(0)
    except OperationalError:
        retry_count += 1
        print(f"Database not ready, retrying... ({retry_count}/{max_retries})")
        time.sleep(1)

print("Could not connect to database")
sys.exit(1)
END

echo ">>> Applying migrations..."
python manage.py migrate --noinput

echo ">>> Creating superuser if not exists..."
python manage.py shell << END
from users.models import User

email = 'admin@pioneer.local'
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email)
    print(f"✅ Superuser created: {email}")
else:
    print(f"ℹ️  Superuser already exists: {email}")
END

echo ">>> Starting server..."
python manage.py runserver 0.0.0.0:8000