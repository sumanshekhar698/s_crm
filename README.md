# S-CRM

A simple customer relationship management (CRM) app built with Django, MySQL and Bootstrap.

## Features

- Landing page with a time-of-day greeting and live customer stats for signed-in users (sample data for visitors)
- Sign up, login / logout and password reset by email, using Django's built-in authentication
- Customers dashboard with search, sortable columns, status filter (Lead / Active / Inactive) and pagination
- Add, view, edit and delete customers; each customer belongs to the user who created it
- Notes timeline on every customer
- CSV export and import
- REST API with Django REST Framework (`/api/`)
- Class-based versions of the customer pages (`/cbv/`) to compare with the function-based views
- Automated tests (`customers/tests.py`)
- Night mode and UI built with Bootstrap 5 and Bootstrap Icons (loaded from CDN, no custom CSS)

## Learning path

Each feature was added in its own commit, so students can step through the history with `git log --oneline` and `git show <commit>`:

| Feature | Django concepts |
| --- | --- |
| `@login_required` refactor | Decorators, `LOGIN_URL`, safe `?next=` redirects |
| Search | `request.GET`, `Q` objects, `icontains` |
| Sortable columns | `order_by()`, whitelisting user input |
| Pagination | `Paginator`, `get_page()`, `{% querystring %}` |
| Home stats | `count()`, date lookups (`created_at__gte`), `timezone` |
| Customer status | `TextChoices`, migrations on an existing table, `get_FOO_display` |
| Record owner | `ForeignKey` to `User`, data migrations (`RunPython`), per-user querysets |
| Notes | A second model, `related_name`, `form.save(commit=False)` |
| CSV export / import | `HttpResponse` downloads, file uploads, reusing a form for validation |
| Password reset | Built-in auth views, email templates, console email backend |
| REST API | Serializers, `ModelViewSet`, routers, API permissions |
| Class-based views | `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`, mixins |
| Tests | `TestCase`, the test client, `setUpTestData`, `mail.outbox` |

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

Password reset emails are printed in this terminal instead of being sent (console email backend).

## Running the tests

```powershell
uv run python manage.py test customers
```

Django creates a temporary `test_crm_db` database, runs the tests and deletes it afterwards, so your real data is untouched. Your MySQL user needs permission to create databases.

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
| `/password-reset/` | Request a password reset email | No |
| `/customers/` | Customers dashboard (`?q=`, `?sort=`, `?status=`, `?page=`) | Yes |
| `/customers/export/` | Download customers as CSV | Yes |
| `/customers/import/` | Upload customers from CSV | Yes |
| `/add_record/` | Add a customer | Yes |
| `/record/<id>/` | Customer details and notes | Yes |
| `/update_record/<id>/` | Edit a customer | Yes |
| `/delete_record/<id>/` | Delete a customer (POST only) | Yes |
| `/cbv/` | Class-based version of the customer pages | Yes |
| `/api/customers/` | REST API (browsable in the browser) | Yes |
| `/logout/` | Logs out (POST only) | Yes |
| `/admin/` | Django admin | Staff only |

Pages that need a login redirect to `/login/?next=...` and return there after you log in.

Regular users only see the customers they created. Superusers see everyone's customers.

## REST API

Browse to http://127.0.0.1:8000/api/customers/ while logged in, or use HTTP Basic auth from the command line:

```powershell
curl.exe -u alice:her-password http://127.0.0.1:8000/api/customers/
curl.exe -u alice:her-password "http://127.0.0.1:8000/api/customers/?q=pune&status=active"
curl.exe -u alice:her-password -H "Content-Type: application/json" -d "{\"first_name\":\"Ana\",\"last_name\":\"Rao\",\"email\":\"ana@example.com\",\"phone\":\"1\",\"address\":\"1 Road\",\"city\":\"Pune\",\"state\":\"MH\",\"zipcode\":\"411001\"}" http://127.0.0.1:8000/api/customers/
```

`GET`, `POST`, `PUT`, `PATCH` and `DELETE` are supported on `/api/customers/` and `/api/customers/<id>/`.

## CSV import format

The first row must be a header. `first_name`, `last_name` and `email` are required columns; `status` is optional (defaults to `lead`):

```
first_name,last_name,email,phone,address,city,state,zipcode,status
Priya,Sharma,priya@example.com,9876543210,12 MG Road,Bengaluru,KA,560001,active
```

Exporting your customers gives you a file in exactly this format.

## Project structure

```
CRM_Django/
├── config/                 # Project settings and root URLs
├── customers/              # Main app
│   ├── migrations/         # Database schema history
│   ├── templates/
│   │   ├── base.html       # Layout, navbar, toasts, footer
│   │   ├── home.html       # Landing page
│   │   └── customers/      # App pages; files starting with _ are partials used with {% include %}
│   │       └── cbv/        # Templates for the class-based views
│   ├── admin.py            # Record and Note admin
│   ├── api.py              # REST API (serializers, viewset, router)
│   ├── cbv_views.py        # Class-based views
│   ├── cbv_urls.py         # /cbv/ URLs (namespace "cbv")
│   ├── forms.py
│   ├── models.py           # Record and Note models
│   ├── tests.py
│   ├── urls.py
│   └── views.py            # Function-based views
├── scripts/create_db.py    # Creates the MySQL database
├── .env.example            # Template for your local .env
├── manage.py
└── pyproject.toml
```
