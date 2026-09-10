import os
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path


def _resolve_db_path():
    db_path = Path(os.getenv("HEALTH_DB_PATH", Path(__file__).resolve().parent / "database.db"))
    db_path = db_path.expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


DB_PATH = _resolve_db_path()
VALID_GOAL_TYPES = {"water", "sleep", "exercise", "weight", "custom"}
VALID_FREQUENCIES = {"daily", "weekly", "custom"}


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _today_iso():
    return datetime.now(timezone.utc).date().isoformat()


def _coerce_iso_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        try:
            return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
        except ValueError:
            raise ValueError("Invalid date value. Please use YYYY-MM-DD.")


def _normalize_goal_type(goal_type):
    normalized = (goal_type or "").strip().lower()
    if normalized not in VALID_GOAL_TYPES:
        raise ValueError("Goal type must be one of: water, sleep, exercise, weight, custom.")
    return normalized


def _normalize_frequency(frequency):
    normalized = (frequency or "daily").strip().lower()
    if normalized not in VALID_FREQUENCIES:
        raise ValueError("Goal frequency must be daily, weekly, or custom.")
    return normalized


def _extract_exercise_minutes(value):
    if value is None:
        return 0.0
    text = str(value).lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(minute|minutes|min|mins|hr|hrs|hour|hours|h)", text)
    if match:
        number = float(match.group(1))
        unit = match.group(2)
        return number * 60 if unit.startswith("h") else number

    numeric_matches = re.findall(r"(\d+(?:\.\d+)?)", text)
    return float(numeric_matches[0]) if numeric_matches else 0.0


def _health_value_for_goal(goal_type, health_row, goal=None):
    if health_row is None:
        return 0.0
    goal_type = str(goal_type).lower()
    if goal_type == "water":
        return float(health_row["water"] or 0)
    if goal_type == "sleep":
        return float(health_row["sleep"] or 0)
    if goal_type == "exercise":
        return float(_extract_exercise_minutes(health_row["exercise"]))
    if goal_type == "weight":
        return float(health_row["weight"] or 0)
    if goal_type == "custom":
        description = " ".join(
            part for part in [goal.get("title") if goal else "", goal.get("unit") if goal else ""] if part
        ).lower()
        if "water" in description or "glass" in description:
            return float(health_row["water"] or 0)
        if "sleep" in description or "hour" in description:
            return float(health_row["sleep"] or 0)
        if "exercise" in description or "minute" in description or "walk" in description:
            return float(_extract_exercise_minutes(health_row["exercise"]))
        if "weight" in description or "kg" in description:
            return float(health_row["weight"] or 0)
        return 0.0
    return 0.0


def goal_progress_for_date(user_id, goal_row, target_date=None):
    target_date = target_date or _today_iso()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM health
            WHERE user_id = ? AND date(recorded_at) = ?
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (user_id, target_date),
        ).fetchone()

    goal_type = str(goal_row.get("goal_type") or goal_row["goal_type"]).lower()
    current_value = _health_value_for_goal(goal_type, row, goal_row)
    target_value = float(goal_row.get("target_value") or 0)
    if target_value <= 0:
        percent = 0.0
        completed = False
    else:
        percent = min(100.0, (current_value / target_value) * 100.0)
        completed = current_value >= target_value
    return {
        "current_value": round(current_value, 2),
        "target_value": round(target_value, 2),
        "percent": round(percent, 1),
        "completed": completed,
        "status": "complete" if completed else "incomplete",
    }


def create_goals_table():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS goals(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_type TEXT NOT NULL,
                title TEXT NOT NULL,
                target_value REAL NOT NULL,
                unit TEXT NOT NULL,
                frequency TEXT DEFAULT 'daily',
                start_date TEXT,
                end_date TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(goals)")}
        if "is_active" not in columns:
            connection.execute("ALTER TABLE goals ADD COLUMN is_active INTEGER DEFAULT 1")
        if "created_at" not in columns:
            connection.execute("ALTER TABLE goals ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_goals_user_active ON goals(user_id, is_active)"
        )
    return True


def add_goal(user_id, goal_type, title, target_value, unit, frequency="daily", start_date=None, end_date=None, is_active=True):
    if not user_id:
        raise ValueError("A valid user_id is required.")
    goal_type = _normalize_goal_type(goal_type)
    title = (title or "").strip()
    if not title:
        raise ValueError("Goal title cannot be empty.")
    target_value = float(target_value)
    if target_value <= 0:
        raise ValueError("Goal target value must be greater than zero.")
    unit = (unit or "").strip()
    if not unit:
        raise ValueError("Goal unit is required.")
    frequency = _normalize_frequency(frequency)
    start_date = _coerce_iso_date(start_date) if start_date else _today_iso()
    end_date = _coerce_iso_date(end_date) if end_date else None
    is_active_value = 1 if is_active else 0

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO goals(user_id, goal_type, title, target_value, unit, frequency, start_date, end_date, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                goal_type,
                title,
                target_value,
                unit,
                frequency,
                start_date,
                end_date,
                is_active_value,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cursor.lastrowid


def get_goals_for_user(user_id, include_inactive=True, target_date=None):
    if not user_id:
        return []
    query = "SELECT * FROM goals WHERE user_id = ?"
    params = [user_id]
    if not include_inactive:
        query += " AND is_active = 1"
    query += " ORDER BY is_active DESC, created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    target_date = target_date or _today_iso()
    goals = []
    for row in rows:
        goal = dict(row)
        goal["goal_type"] = str(goal["goal_type"]).lower()
        goal["is_active"] = bool(goal["is_active"])
        goal["progress"] = goal_progress_for_date(user_id, goal, target_date)
        goals.append(goal)
    return goals


def get_goal_by_id(user_id, goal_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id),
        ).fetchone()
    if row is None:
        return None
    goal = dict(row)
    goal["goal_type"] = str(goal["goal_type"]).lower()
    goal["is_active"] = bool(goal["is_active"])
    goal["progress"] = goal_progress_for_date(user_id, goal)
    return goal


def update_goal(user_id, goal_id, **updates):
    if not goal_id or not user_id:
        raise ValueError("Goal and user identifiers are required.")

    fields = {}
    if "goal_type" in updates and updates["goal_type"] is not None:
        fields["goal_type"] = _normalize_goal_type(updates["goal_type"])
    if "title" in updates and updates["title"] is not None:
        title = str(updates["title"]).strip()
        if not title:
            raise ValueError("Goal title cannot be empty.")
        fields["title"] = title
    if "target_value" in updates and updates["target_value"] is not None:
        target_value = float(updates["target_value"])
        if target_value <= 0:
            raise ValueError("Goal target value must be greater than zero.")
        fields["target_value"] = target_value
    if "unit" in updates and updates["unit"] is not None:
        unit = str(updates["unit"]).strip()
        if not unit:
            raise ValueError("Goal unit is required.")
        fields["unit"] = unit
    if "frequency" in updates and updates["frequency"] is not None:
        fields["frequency"] = _normalize_frequency(updates["frequency"])
    if "start_date" in updates and updates["start_date"] is not None:
        fields["start_date"] = _coerce_iso_date(updates["start_date"]) if updates["start_date"] else _today_iso()
    if "end_date" in updates and updates["end_date"] is not None:
        fields["end_date"] = _coerce_iso_date(updates["end_date"])
    if "is_active" in updates and updates["is_active"] is not None:
        fields["is_active"] = 1 if updates["is_active"] else 0

    if not fields:
        return get_goal_by_id(user_id, goal_id)

    set_sql = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [user_id, goal_id]

    with get_connection() as connection:
        connection.execute(f"UPDATE goals SET {set_sql} WHERE user_id = ? AND id = ?", values)

    return get_goal_by_id(user_id, goal_id)


def delete_goal(user_id, goal_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id),
        )
        return cursor.rowcount > 0


create_goals_table()
