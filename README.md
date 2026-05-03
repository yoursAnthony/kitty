# Kittygram

REST API для учебного проекта **Kittygram** (РЭУ им. Г.В. Плеханова, дисциплина «Интеграция и управление приложениями на удалённом сервере»). Проект построен на **Django 4.2 LTS** и **Django REST Framework 3.14**, использует JWT-аутентификацию через **Djoser**, документируется **drf-spectacular** (Swagger/ReDoc) и разворачивается через **Docker Compose** (Postgres + Gunicorn + Nginx).

В рамках творческого расширения добавляется сценарий **«Мини-чат по заявкам»**: кото-ивенты, заявки на участие и диалог между организатором и участником (см. ветку `feature/creative` после её появления).

---

## Стек

- Python 3.11
- Django 4.2.16
- Django REST Framework 3.14.0
- Djoser 2.2.3 + djangorestframework-simplejwt 5.3.1 (JWT)
- drf-spectacular 0.27.2 (Swagger UI / ReDoc)
- django-filter 24.3 (фильтрация)
- Pillow 10.4 (изображения)
- PostgreSQL 16 (в проде / docker-compose), SQLite (опционально для локальной разработки)
- Gunicorn 23 + Nginx 1.25 (в docker-compose)

---

## Что есть в API

| URL | Метод | Описание | Доступ |
|---|---|---|---|
| `/api/v1/auth/users/` | POST | Регистрация пользователя | public |
| `/api/v1/auth/users/me/` | GET / PATCH | Профиль текущего пользователя | JWT |
| `/api/v1/auth/jwt/create/` | POST | Получить пару JWT (access + refresh) | public |
| `/api/v1/auth/jwt/refresh/` | POST | Обновить access по refresh | public |
| `/api/v1/auth/jwt/verify/` | POST | Проверить access | public |
| `/api/v1/cats/` | GET | Список котов (фильтр, поиск, пагинация) | public |
| `/api/v1/cats/` | POST | Создать кота (owner = `request.user`) | JWT |
| `/api/v1/cats/{id}/` | GET / PATCH / DELETE | CRUD конкретного кота | owner-only на write |
| `/api/v1/cats/{id}/upload_image/` | POST | Загрузить фото (multipart) | owner |
| `/api/v1/achievements/` | GET / POST | Справочник достижений | GET public, POST staff |
| `/api/v1/tags/` | GET | Справочник тегов | public |
| `/api/schema/` | GET | OpenAPI 3.0 схема (YAML) | public |
| `/api/schema/swagger-ui/` | GET | Swagger UI | public |
| `/api/schema/redoc/` | GET | ReDoc | public |

**Параметры списочных эндпоинтов:**
- Фильтрация: `?owner=<username>`, `?tag=<slug>`, `?birth_year_min=2018`, `?birth_year_max=2024`
- Поиск: `?search=<строка>` (поля: name, color, description)
- Сортировка: `?ordering=-created_at` (доступны: `created_at`, `birth_year`, `name`)
- Пагинация: `?page=2&page_size=20` (по умолчанию 10, максимум 100)

**Throttling:** анонимные — 50 запросов/час, авторизованные — 1000 запросов/час.

---

## Быстрый старт через Docker Compose (рекомендуется)

Требуется: Docker Desktop (Windows/macOS) или Docker Engine + docker-compose-plugin (Linux).

```bash
# 1. Клонировать репозиторий
git clone https://github.com/yoursAnthony/kitty.git
cd kitty

# 2. Скопировать .env.example в .env и заполнить
#    На Windows (PowerShell):
copy .env.example .env
#    На Linux/macOS:
cp .env.example .env
#    Затем отредактировать .env: задать SECRET_KEY и POSTGRES_PASSWORD.

# 3. Поднять стек (postgres + backend + nginx)
docker compose up -d --build

# 4. Создать суперпользователя
docker compose exec backend python manage.py createsuperuser

# 5. Проверить, что API живой
curl http://localhost/api/v1/cats/
# {"count":0,"next":null,"previous":null,"results":[]}

# 6. Открыть Swagger UI в браузере
#    http://localhost/api/schema/swagger-ui/
```

Остановить стек: `docker compose down`. Удалить вместе с volumes (БД, статика, медиа): `docker compose down -v`.

---

## Локальный запуск без Docker

Подходит для разработки. По умолчанию используется PostgreSQL — для совсем быстрого старта можно переключиться на SQLite (флаг `USE_SQLITE=1`).

```bash
# 1. Создать виртуальное окружение
python -m venv .venv

# Активировать (Windows PowerShell):
.\.venv\Scripts\Activate.ps1
# Активировать (Linux/macOS):
source .venv/bin/activate

# 2. Установить зависимости
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Создать .env (см. ниже минимальный набор для SQLite)
copy .env.example .env

# Минимальный .env для запуска на SQLite:
#   SECRET_KEY=dev-secret-not-for-prod
#   DEBUG=True
#   ALLOWED_HOSTS=localhost,127.0.0.1
#   USE_SQLITE=1

# 4. Применить миграции
python manage.py migrate

# 5. Создать суперпользователя
python manage.py createsuperuser

# 6. Запустить dev-сервер
python manage.py runserver
# API доступен на http://127.0.0.1:8000/api/v1/cats/
# Swagger:    http://127.0.0.1:8000/api/schema/swagger-ui/
```

---

## Переменные окружения (`.env`)

| Переменная | Назначение | Пример |
|---|---|---|
| `SECRET_KEY` | Секретный ключ Django (обязательно сменить на проде) | `xy7f...` |
| `DEBUG` | Включить debug-режим | `False` |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую | `localhost,127.0.0.1,example.ru` |
| `USE_SQLITE` | Использовать SQLite вместо PostgreSQL | `0` или `1` |
| `POSTGRES_DB` | Имя БД PostgreSQL | `kittygram` |
| `POSTGRES_USER` | Пользователь PostgreSQL | `kittygram` |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `strong-password` |
| `DB_HOST` | Хост БД (в docker-compose — `db`) | `db` |
| `DB_PORT` | Порт БД | `5432` |

Секреты в репозиторий **не коммитятся** — `.env` уже в `.gitignore`. Образец — в `.env.example`.

---

## Структура репозитория

```
kitty/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
├── nginx/
│   └── default.conf            # nginx-конфиг (reverse proxy + статика)
├── kittygram/                  # Django-настройки проекта
│   ├── settings.py             # читает env-переменные
│   └── urls.py                 # роутинг + Swagger + Djoser JWT
├── cats/                       # приложение Kittygram
│   ├── models.py               # Cat, Tag, Achievement, CatTag, CatAchievement
│   ├── serializers.py
│   ├── views.py                # CatViewSet, AchievementViewSet, TagViewSet
│   ├── filters.py
│   ├── urls.py
│   └── migrations/
├── core/                       # общие утилиты
│   ├── permissions.py          # IsOwnerOrReadOnly
│   └── pagination.py           # DefaultPagination(10)
└── postman/
    └── kittygram.postman_collection.json
```

---

## Тестирование API

В каталоге `postman/` лежит коллекция **`kittygram.postman_collection.json`** (формат v2.1) с готовыми запросами: регистрация → JWT → CRUD котов → загрузка фото → негативные кейсы. После импорта в Postman:
1. Создайте окружение с переменной `base_url` = `http://localhost` (через docker-compose) или `http://127.0.0.1:8000` (локально).
2. Запустите по порядку запросы из папки `Auth` — JWT сохранится в коллекционную переменную `access_token`.
3. Дальше прогоняйте запросы из папок `Cats`, `Achievements`, `Tags`.

Альтернатива — `curl`/`httpie`, примеры есть в Swagger UI.

---

## Лицензия

MIT — см. `LICENSE`.
