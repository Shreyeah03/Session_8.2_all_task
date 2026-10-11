# TaskPro - Personal Task Management App

Django + Django REST Framework + MySQL, JWT auth (djangorestframework-simplejwt),
and a Bootstrap 5 + Fetch API frontend. Each user sees only their own tasks.

## Setup

```bash
python -m venv venv
source venv/bin/activate         
pip install -r requirements.txt

# 1. Create the MySQL database
mysql -u root -p -e "CREATE DATABASE taskpro CHARACTER SET utf8mb4;"

# 2. Set DB credentials (env vars, see .env.example)
export DB_USER=root DB_PASSWORD=your-mysql-password

# 3. Migrate and start
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/ and register an account.

No MySQL handy? Add `USE_SQLITE=1` before the migrate and runserver commands to use SQLite.
Run tests with `USE_SQLITE=1 python manage.py test`.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/auth/register/ | Create account, returns access + refresh tokens |
| POST | /api/auth/login/ | Returns access + refresh tokens |
| POST | /api/auth/refresh/ | New access token |
| GET | /api/auth/me/ | Current user |
| GET | /api/tasks/ | List own tasks |
| POST | /api/tasks/ | Create task |
| GET/PATCH/PUT/DELETE | /api/tasks/ID/ | Read, edit, delete |
| POST | /api/tasks/ID/complete/ | Mark as completed |

Send `Authorization: Bearer <access>` on task endpoints.

List params: status=all|pending|completed, priority=low|medium|high,
search=text in title, ordering=due_date (default, ascending) or -due_date.
# Session_8.2_Major_Project
