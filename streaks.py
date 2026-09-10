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


def _goal_value_for_day(user_id, goal, check_date):
    goal_type = str(goal["goal_type"]).lower()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM health
            WHERE user_id = ? AND date(recorded_at) = ?
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (user_id, check_date.isoformat()),
        ).fetchone()
    if row is None:
        return 0.0
    if goal_type == "water":
        return float(row["water"] or 0)
    if goal_type == "sleep":
        return float(row["sleep"] or 0)
    if goal_type == "exercise":
        exercise = str(row["exercise"] or "")
        number_str = "".join(ch for ch in exercise if ch.isdigit() or ch in ".")
        return float(number_str) if number_str else 0.0
    if goal_type == "weight":
        return float(row["weight"] or 0)
    return 0.0


def _goal_completed_on_day(user_id, goal, check_date):
    current_value = _goal_value_for_day(user_id, goal, check_date)
    target_value = float(goal.get("target_value") or 0)
    return target_value > 0 and current_value >= target_value


def calculate_goal_streak(user_id, goal_id):
    goals = get_goals_for_user(user_id, include_inactive=True)
    goal = next((item for item in goals if item["id"] == goal_id), None)
    if goal is None:
        return {"current_streak": 0, "longest_streak": 0, "last_completed_date": None}

    today = date.today()
    current_streak = 0
    check_date = today
    while _goal_completed_on_day(user_id, goal, check_date):
        current_streak += 1
        check_date -= timedelta(days=1)

    longest_streak = 0
    loop_date = today
    streak = 0
    while loop_date >= date(2000, 1, 1):
        if _goal_completed_on_day(user_id, goal, loop_date):
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0
        loop_date -= timedelta(days=1)

    last_completed_date = None
    lookup_day = today
    while lookup_day >= date(2000, 1, 1):
        if _goal_completed_on_day(user_id, goal, lookup_day):
            last_completed_date = lookup_day.isoformat()
            break
        lookup_day -= timedelta(days=1)

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "last_completed_date": last_completed_date,
    }


def calculate_user_streak_summary(user_id):
    goals = get_goals_for_user(user_id, include_inactive=True)
    if not goals:
        return {"current_streak": 0, "longest_streak": 0, "last_completed_date": None}

    today = date.today()
    current_streaks = []
    overall_best = 0
    for goal in goals:
        goal_summary = calculate_goal_streak(user_id, goal["id"])
        current_streaks.append(goal_summary["current_streak"])
        overall_best = max(overall_best, goal_summary["longest_streak"])

    current_streak = max(current_streaks) if current_streaks else 0
    last_completed_date = None
    lookup_day = today
    while lookup_day >= date(2000, 1, 1):
        for goal in goals:
            if _goal_completed_on_day(user_id, goal, lookup_day):
                last_completed_date = lookup_day.isoformat()
                break
        if last_completed_date is not None:
            break
        lookup_day -= timedelta(days=1)

    return {
        "current_streak": current_streak,
        "longest_streak": overall_best,
        "last_completed_date": last_completed_date,
    }
