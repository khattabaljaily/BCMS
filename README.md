# BCMS

Beauty Center Management System (BCMS) is a Django-based web application for managing salon and spa center operations.

## Key features

- Authentication, registration, and user session management
- Center-aware multi-tenant support via `request.center`
- Appointments, services, clients, billing, finance, products, and reporting modules
- Reports page with KPI dashboards, charts, and browser-based PDF export
- Print-friendly export view with site styling and no navigation controls
- Static asset handling via WhiteNoise

## Requirements

- Python 3.12+
- Django 4.2.7
- MySQL client for database connectivity

## Setup

1. Create a virtual environment and activate it:

```bash
python -m venv .env
source .env/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `secrets.json` file in the project root with your environment settings. At minimum, include:

```json
{
  "SECRET_KEY": "your-secret-key",
  "DEBUG": true,
  "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
  "DATABASE": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": "db.sqlite3"
  }
}
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Collect static files:

```bash
python manage.py collectstatic --noinput
```

6. Start the development server:

```bash
python manage.py runserver
```

## Notes

- Use the `/reports/print/?auto_print=1` path for print-ready report export.
- The app uses `apps.core.middleware.CenterMiddleware` to attach `request.center` to authenticated users.
- If you update dependencies, rerun `pip install -r requirements.txt` after regenerating the file.
