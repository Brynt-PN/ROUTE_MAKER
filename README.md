# ROUTE_MAKER
ROUTE_MAKER  is a project created to simplify the logistical task of creating dispatch routes, taking into account factors such as time, distance, maximum number of points per route, etc.

Create a `.env` file from `.env.example` and configure `DJANGO_SECRET_KEY` and `GEOAPIFY_API_KEY` before running the project.

Optional Geoapify autocomplete tuning:

```env
GEOAPIFY_AUTOCOMPLETE_LANG=es
GEOAPIFY_AUTOCOMPLETE_COUNTRY_BIAS=pe
GEOAPIFY_AUTOCOMPLETE_COUNTRY_FILTER=
```

## Local development

Use a local virtual environment and SQLite for the first development pass:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python Route_Maker\manage.py migrate
python Route_Maker\manage.py runserver
```

## Local pre-deploy checklist

To leave the project ready for Railway + Neon from local development:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python Route_Maker\manage.py check
python Route_Maker\manage.py collectstatic --noinput
```

The project now supports:

- `SQLite` by default for quick local development
- `DATABASE_URL` for Neon / Railway
- classic `POSTGRES_*` variables for local PostgreSQL
- `gunicorn` for production start
- `WhiteNoise` for static files

If later you want to switch to PostgreSQL, configure either `DATABASE_URL` or these environment variables in `.env`:

```env
POSTGRES_DB_NAME=
POSTGRES_DB_USER=
POSTGRES_DB_PASSWORD=
POSTGRES_DB_HOST=localhost
POSTGRES_DB_PORT=5432
```

Example Railway start command:

```text
gunicorn Route_Maker.wsgi --chdir Route_Maker --bind 0.0.0.0:$PORT
```
