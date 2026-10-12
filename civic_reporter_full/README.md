# GroundTruth — Civic Issue Reporter

A Django REST Framework project with a static HTML/CSS/JavaScript frontend. Citizens can create accounts, file neighborhood issue reports, attach an optional photo, comment, upvote, and follow status history. Authorities can be assigned an `AuthorityProfile` and manage reports in their assigned area. Administrators manage areas, categories, users, and reports through Django admin.

## Local setup

Requires Python 3.10–3.12 (use a version supported by the selected Django release).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
copy .env.example .env   # Windows PowerShell; on macOS/Linux use: cp .env.example .env
python manage.py makemigrations accounts reports
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Admin is at `/admin/`. Create some Areas and Categories in admin before filing a report. Create an AuthorityProfile for an authority user and assign its area. Keep `.env`, `db.sqlite3`, uploaded media, and production secrets out of Git.

## Deployment checklist

1. Set `DEBUG=false`, a long random `SECRET_KEY`, and exact `ALLOWED_HOSTS` (hostnames only, comma-separated).
2. Set `DATABASE_URL` to a managed PostgreSQL database. Ensure the host installs `requirements.txt` and uses `gunicorn civic_reporter.wsgi:application` (Procfile included).
3. Run `python manage.py migrate` and `python manage.py collectstatic --noinput` as release/build steps. Create a superuser securely.
4. Set persistent media storage for user-uploaded photos. Local filesystem media may be lost on ephemeral hosting; use object storage or a persistent disk.
5. If hosting frontend separately, set `API_BASE_OVERRIDE` in `frontend/js/api.js` to `https://YOUR-BACKEND/api`, set backend `CORS_ALLOWED_ORIGINS` to the exact frontend origin(s), and use HTTPS for both. Do not use `file://` for production testing.
6. Add your backend origin to `CSRF_TRUSTED_ORIGINS` only if needed for Django admin/session flows. Test `https://YOUR-BACKEND/admin/`, `/api/auth/register/`, `/api/auth/login/`, `/api/reports/areas/`, `/api/reports/categories/`, and report creation.
7. Run `python manage.py check --deploy` and fix any deployment warnings before launch.

## API overview

- `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/token/refresh/`, `GET /api/auth/me/`
- `GET /api/reports/areas/`, `GET /api/reports/categories/` (authenticated read; staff/admin writes)
- `GET /api/reports/`, `POST /api/reports/`, `GET /api/reports/mine/`, `GET /api/reports/{id}/`
- `POST /api/reports/{id}/comments/`, `POST /api/reports/{id}/upvote/`, `POST /api/reports/{id}/verify/`, `POST /api/reports/{id}/set_status/`
- `GET /api/reports/notifications/`

## Important limitations

This is a project starter, not a security-audited civic platform. Before handling real public submissions, configure rate limits and backups, use durable object storage and database backups, add moderation/abuse workflows, validate image dimensions/content and malware risks, establish privacy/retention policies, and test authority access rules with your actual workflow. Email notifications, password reset, and a public map view are not included yet.

### Database migrations before deployment

This source bundle intentionally includes the model definitions and tests, but generated migration files must be created for your current schema before a production deployment. From the project root, run `python manage.py makemigrations accounts reports` and `python manage.py migrate`, then keep the generated `accounts/migrations/` and `reports/migrations/` files in Git. Do not deploy a new schema without its migrations.
