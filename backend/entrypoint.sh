#!/bin/sh
set -e

echo "==> Creating database if it does not exist..."
python -c "
import psycopg2, os, urllib.parse
url = os.environ.get('DATABASE_URL', '')
if url:
    p = urllib.parse.urlparse(url)
    try:
        conn = psycopg2.connect(host=p.hostname, port=p.port or 5432,
                                user=p.username, password=p.password,
                                database='postgres')
        conn.autocommit = True
        cur = conn.cursor()
        dbname = p.path.lstrip('/')
        cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (dbname,))
        if not cur.fetchone():
            cur.execute('CREATE DATABASE \"' + dbname + '\"')
            print('Created database:', dbname)
        else:
            print('Database already exists:', dbname)
        conn.close()
    except Exception as e:
        print('DB create error:', e)
"

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Creating superuser if not exists..."
python manage.py createsuperuser --noinput || true

echo "==> Starting gunicorn..."
exec gunicorn wecare.wsgi:application --bind 0.0.0.0:8000 --timeout 300
