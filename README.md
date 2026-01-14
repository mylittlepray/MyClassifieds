# MyClassifieds

Django-проект доски объявлений (backend).

## Возможности (кратко)
- Веб-приложение на Django.
- Отправка почтовых уведомлений через SMTP.
- Продакшн-запуск через Gunicorn + Nginx.
- Redis для кэша/очередей (если используется в проекте).

---

## Требования

Рекомендуемая ОС: Ubuntu 22.04+/Debian 11+.

### Пакеты
- Python 3.10+ (можно 3.11)
- Git
- Nginx
- Redis
- (Рекомендуется) PostgreSQL
- build tools для сборки зависимостей

---

## Установка и запуск (Linux)

### 1) Установка системных пакетов

```bash
sudo apt update
sudo apt install -y \
  git python3 python3-venv python3-dev build-essential \
  nginx redis-server \
  libpq-dev postgresql postgresql-contrib
```

Проверь, что сервисы стартуют:
```bash
sudo systemctl enable --now redis-server
sudo systemctl status redis-server
sudo systemctl enable --now nginx
sudo systemctl status nginx
```

---

### 2) Клонирование проекта

```bash
cd /srv
sudo git clone https://github.com/mylittlepray/MyClassifieds.git
cd MyClassifieds
```

> Лучше держать проект в `/srv/MyClassifieds` или `/var/www/MyClassifieds`.

---

### 3) Виртуальное окружение + зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip wheel
```

Установка зависимостей:
```bash
pip install -r requirements.txt
```

Если `requirements.txt` отсутствует и проект на Poetry/pyproject:
```bash
pip install poetry
poetry install
```

---

## Настройка окружения (.env)

### 1) Создай файл `.env` из шаблона

```bash
cp env.template .env
nano .env
```

### 2) Что нужно заполнить в `.env`

Пример (смысл полей):

```env
DJANGO_SECRET_KEY='СЮДА_СЛОЖНЫЙ_СЕКРЕТНЫЙ_КЛЮЧ'
ALLOWED_HOSTS='yourdomain.com,www.yourdomain.com,123.123.123.123'

DEFAULT_FROM_EMAIL="noreply@yourdomain.com"
MAILERSEND_HOST='smtp.mailersend.net'   # или SMTP хост вашего провайдера
MAILERSEND_USER='user'                 # логин SMTP
MAILERSEND_KEY='pass or apikey'        # пароль/апикей SMTP
```

**Важно:**
- `DJANGO_SECRET_KEY` должен быть уникальным и длинным.
- `ALLOWED_HOSTS` — домены и IP через запятую без пробелов.
- `DEFAULT_FROM_EMAIL` — адрес отправителя “по умолчанию”.
- `MAILERSEND_*` — SMTP креды (необязательно MailerSend — можно любой SMTP, если настройки в `settings.py` совпадают).

---

## Настройки в settings.py (что заменить на свои)

Ниже — чеклист типовых продакшн-настроек (названия могут отличаться — смотри свой `settings.py`).

### Обязательное
- `SECRET_KEY` → брать из переменной окружения `DJANGO_SECRET_KEY`
- `DEBUG = False` в продакшне
- `ALLOWED_HOSTS` → из `.env`
- `DATABASES` → свои доступы (PostgreSQL/SQLite)
- `STATIC_URL`, `STATIC_ROOT` (обычно `/static/`, `/var/www/.../static/`)
- `MEDIA_URL`, `MEDIA_ROOT` (если есть загрузка файлов)
- `CSRF_TRUSTED_ORIGINS` → домены вида `https://yourdomain.com`

### Почта (SMTP)
Настрой email через переменные окружения (примерно так):

```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("MAILERSEND_HOST")
EMAIL_HOST_USER = env("MAILERSEND_USER")
EMAIL_HOST_PASSWORD = env("MAILERSEND_KEY")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
```

> Если у провайдера порт/SSL другие — выстави корректно `EMAIL_PORT` и `EMAIL_USE_TLS/EMAIL_USE_SSL`.

### Redis (если используется)
Типовые варианты:

**Кэш:**
```python
CACHES = {
  "default": {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": "redis://127.0.0.1:6379/1",
    "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
  }
}
```

**Celery (если есть фоновые задачи):**
```python
CELERY_BROKER_URL = "redis://127.0.0.1:6379/2"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/3"
```

---

## База данных и миграции

### PostgreSQL (рекомендуется)

Создай пользователя и базу:
```bash
sudo -u postgres psql
```

В psql:
```sql
CREATE DATABASE myclassifieds;
CREATE USER myclassifieds_user WITH PASSWORD 'strong_password';
ALTER ROLE myclassifieds_user SET client_encoding TO 'utf8';
ALTER ROLE myclassifieds_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE myclassifieds_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE myclassifieds TO myclassifieds_user;
\q
```

Далее пропиши доступы в `settings.py`/`.env` (как у тебя реализовано).

### Миграции + суперюзер

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
```

---

## Static/Media

Собери статику:
```bash
python manage.py collectstatic --noinput
```

Убедись, что в `settings.py` задан `STATIC_ROOT`, например:
- `/var/www/myclassifieds/static/`

---

## Gunicorn (prod)

### 1) Установка gunicorn

```bash
source .venv/bin/activate
pip install gunicorn
```

### 2) Проверь имя WSGI-модуля

Найди файл `wsgi.py` в проекте:
- обычно путь вроде `<django_project_name>/wsgi.py`

Тогда WSGI import будет:
- `<django_project_name>.wsgi:application`

### 3) systemd unit

Создай пользователя (опционально):
```bash
sudo useradd -r -s /bin/false myclassifieds || true
```

Сервис-файл:
```bash
sudo nano /etc/systemd/system/myclassifieds.service
```

Содержимое (замени пути и `<django_project_name>`):
```ini
[Unit]
Description=MyClassifieds Gunicorn
After=network.target

[Service]
User=myclassifieds
Group=www-data
WorkingDirectory=/srv/MyClassifieds
Environment="PATH=/srv/MyClassifieds/.venv/bin"
EnvironmentFile=/srv/MyClassifieds/.env

ExecStart=/srv/MyClassifieds/.venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/run/myclassifieds.sock \
  <django_project_name>.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Создай директорию под сокет (если нужно):
```bash
sudo mkdir -p /run
sudo chown myclassifieds:www-data /run
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myclassifieds
sudo systemctl status myclassifieds
```

Логи:
```bash
sudo journalctl -u myclassifieds -f
```

---

## Nginx (prod)

Создай конфиг:
```bash
sudo nano /etc/nginx/sites-available/myclassifieds
```

Пример (замени домен и пути):
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20m;

    location /static/ {
        alias /var/www/myclassifieds/static/;
        expires 7d;
    }

    location /media/ {
        alias /var/www/myclassifieds/media/;
        expires 7d;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_pass http://unix:/run/myclassifieds.sock;
    }
}
```

Включи сайт и проверь конфиг:
```bash
sudo ln -s /etc/nginx/sites-available/myclassifieds /etc/nginx/sites-enabled/myclassifieds
sudo nginx -t
sudo systemctl reload nginx
```

---

## SMTP (почтовые уведомления)

### Что нужно у SMTP-провайдера
- SMTP host (пример: `smtp.mailersend.net`)
- SMTP login
- SMTP password/API key
- Порт 587 (TLS) — чаще всего

### Частые причины “не отправляет”
- Неверный `DEFAULT_FROM_EMAIL` (домен не подтвержден у провайдера)
- Закрыт исходящий порт 587 на сервере/хостинге
- `ALLOWED_HOSTS` не содержит реальный домен
- `DEBUG=False`, но не настроены логи/ошибки скрываются

---

## Redis

Проверка:
```bash
redis-cli ping
# должен ответить: PONG
```

Если Redis нужен для кэша/очередей — убедись, что соответствующие настройки включены в `settings.py`.

---

## Проверка работоспособности

1) Временно запусти dev-сервер:
```bash
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

2) Проверь сайт: `http://<server-ip>:8000`

3) После этого переходи на Gunicorn + Nginx.

---

## Безопасность (рекомендации для prod)
- Всегда `DEBUG=False` и уникальный `DJANGO_SECRET_KEY`.
- Добавь HTTPS (certbot/Let’s Encrypt) и `CSRF_TRUSTED_ORIGINS`.
- Не коммить `.env` и секреты.