# Pulseboard — personal health tracker

A FastAPI + SQLite application for logging daily wellness data and seeing progress on one dashboard. Register, sign in, log weight / water / sleep / exercise, get BMI analysis, set goals, track streaks, and review history.

---

## Features

**Accounts**
- Registration and login
- Password hashing with PBKDF2-SHA256

**Daily logging**
- Weight, water intake, sleep hours, exercise and movement notes
- Dashboard metrics for the latest entry, plus recent history

**Analysis**
- BMI calculation with category, ideal weight range and health recommendations
- Goal setting with progress tracking
- Streaks, computed per goal
- Calendar view of logged days

**Frontend**
- Responsive browser UI (desktop and mobile) served by the app
- Personal wellness to-do list, scoped per user

## API

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Serves the frontend |
| `POST` | `/signup` | Create an account |
| `POST` | `/login` | Authenticate |
| `GET` | `/dashboard/{user_id}` | Health records for the dashboard |
| `POST` | `/health` | Save a health entry |
| `GET` | `/bmi` | BMI, category, ideal range and recommendations |
| `POST` | `/goals` | Create a goal |
| `GET` | `/goals` | List goals |
| `GET` | `/goals/{goal_id}` | Fetch one goal |
| `PUT` | `/goals/{goal_id}` | Update a goal |
| `DELETE` | `/goals/{goal_id}` | Delete a goal |
| `GET` | `/streaks` | Streaks across goals |
| `GET` | `/streaks/{goal_id}` | Streak for one goal |
| `GET` | `/calendar` | Days with logged data |
| `GET` | `/calendar/{date}` | Entries for a specific date |

Incoming payloads are validated with Pydantic models.

## Project layout

```
app.py              FastAPI application and all API routes
auth.py             registration, login, PBKDF2-SHA256 hashing
tracker.py          health database operations and validation
analytics.py        health record retrieval
BMI_cal.py          BMI calculations and health tips
goals.py            goal CRUD
streaks.py          streak computation across goals
calendar_api.py     calendar endpoints
dashboard.py        dashboard data assembly
sleep.py            sleep logging
water.py            water logging
exercise.py         exercise logging
setup.py            database initialisation helper
frontend/
  index.html        application interface
  styles.css        responsive styling
  app.js            frontend behaviour and API calls
feature_smoke_test.py   end-to-end smoke test
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python setup.py                      # initialise the database
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/` — interactive API docs at `/docs`.

The database path can be overridden with the `HEALTH_DB_PATH` environment variable.

## Stack

Python · FastAPI · Pydantic · SQLite · Uvicorn · Pandas · HTML / CSS / JavaScript

---

*Built by [Pankaj Prasad](https://github.com/pankajprasad2408-runner) — 2nd-year B.Tech (AI & Data Science), Arya College of Engineering, Jaipur.*
