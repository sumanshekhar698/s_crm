# S-CRM

A simple customer relationship management (CRM) app built with Django, MySQL and Bootstrap.

## Features

- Landing page with a time-of-day greeting and an overview widget (sample data)
- Login / logout using Django's built-in authentication
- Customers dashboard listing all records, visible only to logged-in users
- Manage customer records from the Django admin
- UI built with Bootstrap 5 and Bootstrap Icons (loaded from CDN, no custom CSS)

## Tech stack

- Python 3.12+
- Django 6.1
- MySQL (via `mysqlclient`)
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

### 1. Install dependencies

```powershell
uv sync
```

### 2. Configure your `.env`

Secrets (the Django secret key and your MySQL password) are kept out of the code in a `.env` file, which git ignores. Copy the template and fill in your own values:

```powershell
Copy-Item .env.example .env
```

`config/settings.py` reads these values with `python-dotenv`.

### 3. Create the MySQL database

```powershell
uv run python scripts/create_db.py
```

or in MySQL directly:

```sql
CREATE DATABASE crm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Create the tables

```powershell
uv run python manage.py migrate
```

### 5. Create an admin user

```powershell
uv run python manage.py createsuperuser
```

### 6. Run the server

```powershell
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Database migrations

This project uses Django's built-in migration system (not Alembic, which is for SQLAlchemy). Django reads the models in `customers/models.py` and generates the database schema from them.

Whenever you add, remove or change a model field:

```powershell
uv run python manage.py makemigrations customers
uv run python manage.py migrate
```

- `makemigrations` writes a new file in `customers/migrations/` describing the change. Commit these files to git.
- `migrate` applies any unapplied migrations to the database.

To see which migrations have been applied:

```powershell
uv run python manage.py showmigrations
```

### Troubleshooting

`(1146, "Table 'crm_db.customers_record' doesn't exist")` means the migrations haven't been applied to your database. Run `uv run python manage.py migrate`.

## Pages

| URL | Description | Login required |
| --- | --- | --- |
| `/` | Landing page | No |
| `/login/` | Login form | No |
| `/signup/` | Create an account (logs you in and opens the dashboard) | No |
| `/customers/` | Customers dashboard | Yes (redirects to `/login/`) |
| `/logout/` | Logs out (POST only) | Yes |
| `/admin/` | Django admin, add and edit customers | Staff only |

## Adding customers

1. Log in at `/admin/` with your superuser account.
2. Open **Records** and click **Add record**.
3. New customers appear on the `/customers/` dashboard.

## Project structure

```
CRM_Django/
├── config/                 # Project settings and root URLs
├── customers/              # Main app
│   ├── migrations/         # Database schema history
│   ├── templates/
│   │   ├── base.html       # Layout, navbar, flash messages
│   │   ├── home.html       # Landing page
│   │   └── customers/
│   │       ├── dashboard.html
│   │       └── login.html
│   ├── admin.py            # Record admin
│   ├── forms.py
│   ├── models.py           # Record model
│   ├── urls.py
│   └── views.py
├── manage.py
└── pyproject.toml
```
