# Pulseboard Health Tracker

Pulseboard is a personal health-tracking application that helps users record daily wellness information and understand their progress in one simple dashboard.

The project combines a FastAPI backend, SQLite storage, and a responsive browser frontend. Users can create an account, sign in, log health data, calculate BMI, review previous entries, and manage a personal list of wellness tasks.

## Features

- User registration and login
- Secure password hashing with PBKDF2-SHA256
- Daily health logging for:
  - Weight
  - Water intake
  - Sleep duration
  - Exercise or movement notes
- Dashboard metrics for the latest health data
- Recent health-entry history
- BMI calculation with:
  - BMI category
  - Ideal weight range
  - Health recommendations
- Personal to-do list with add, complete, and remove actions
- Responsive layout for desktop and mobile screens
- SQLite database persistence for user accounts and health records

## Technology

- Python
- FastAPI
- Pydantic
- SQLite
- Pandas
- HTML, CSS, and JavaScript
- Uvicorn

## Project Structure

```text
HEALTH/
├── app.py              # FastAPI application and API routes
├── auth.py             # User registration, login, and password hashing
├── tracker.py          # Health database operations and validation
├── analytics.py        # Health record retrieval
├── BMI_cal.py          # BMI calculations and health tips
├── frontend/
│   ├── index.html      # Application interface
│   ├── styles.css      # Responsive styling
│   └── app.js          # Frontend behavior and API requests
└── setup.py            # Database initialization helper
```

## Run the Application

From the project directory, start the FastAPI server with the project virtual environment:

```powershell
.\myvenv\Scripts\python.exe -m uvicorn app:app --reload
```

Open the application at:

```text
http://127.0.0.1:8000/
```

The interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## API Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/signup` | Create a user account |
| `POST` | `/login` | Authenticate a user |
| `GET` | `/dashboard/{user_id}` | Retrieve health records |
| `POST` | `/health` | Save a health entry |
| `GET` | `/bmi` | Calculate BMI and recommendations |

## Notes

Health records and user accounts are stored in SQLite. The current to-do list is stored in the browser's local storage and is separated by user ID.
