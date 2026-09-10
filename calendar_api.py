import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from goals import get_goals_for_user


def _resolve_db_path():
    db_path = Path(os.getenv("HEALTH_DB_PATH", Path(__file__).resolve().parent / "database.db"))
    db_path = db_path.expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


DB_PATH = _resolve_db_path()


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def create_calendar_table():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS calendar_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                summary TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_calendar_user_date ON calendar_events(user_id, event_date)"
        )
    return True


def _completed_goals_for_date(user_id, target_date):
    goals = get_goals_for_user(user_id, include_inactive=True, target_date=target_date)
    count = 0
    for goal in goals:
        if goal["progress"].get("completed"):
            count += 1
    return count, len(goals)


def get_calendar_month(user_id, year, month):
    year = int(year)
    month = int(month)
    first_day = date(year, month, 1)
    next_month = date(year + (month // 12), (month % 12) + 1, 1) if month < 12 else date(year + 1, 1, 1)
    days_in_month = (next_month - timedelta(days=1)).day
    entries = []
    for day in range(1, days_in_month + 1):
        current_day = date(year, month, day)
        goals_completed, total_goals = _completed_goals_for_date(user_id, current_day.isoformat())
        if total_goals == 0:
            status = "none"
        elif goals_completed == 0:
            status = "missed"
        elif goals_completed == total_goals:
            status = "completed"
        else:
            status = "partial"
        entries.append({
            "date": current_day.isoformat(),
            "status": status,
            "goals_completed": goals_completed,
            "total_goals": total_goals,
        })
    return {"year": year, "month": month, "days": entries, "first_weekday": first_day.weekday()}


def get_day_summary(user_id, target_date):
    try:
        selected_day = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Invalid date. Use YYYY-MM-DD format.") from exc

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM health
            WHERE user_id = ? AND date(recorded_at) = ?
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (user_id, selected_day.isoformat()),
        ).fetchone()

    goals = get_goals_for_user(user_id, include_inactive=True, target_date=selected_day.isoformat())
    details = {
        "date": selected_day.isoformat(),
        "weight": float(row["weight"]) if row and row["weight"] is not None else None,
        "water": int(row["water"]) if row and row["water"] is not None else 0,
        "sleep": float(row["sleep"]) if row and row["sleep"] is not None else 0.0,
        "exercise": str(row["exercise"] or "") if row else "",
        "goals": [],
        "goals_completed": 0,
        "total_goals": len(goals),
        "status": "none",
    }

    for goal in goals:
        progress = goal["progress"]
        details["goals"].append({
            "id": goal["id"],
            "title": goal["title"],
            "goal_type": goal["goal_type"],
            "target_value": goal["target_value"],
            "unit": goal["unit"],
            "completed": progress["completed"],
            "percent": progress["percent"],
        })
        if progress["completed"]:
            details["goals_completed"] += 1

    if details["total_goals"] == 0:
        details["status"] = "none"
    elif details["goals_completed"] == 0:
        details["status"] = "missed"
    elif details["goals_completed"] == details["total_goals"]:
        details["status"] = "completed"
    else:
        details["status"] = "partial"

    return details


create_calendar_table()
