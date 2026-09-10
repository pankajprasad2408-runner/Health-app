import sqlite3

from auth import signup
from calendar_api import create_calendar_table, get_calendar_month
from goals import add_goal, create_goals_table, get_goals_for_user
from streaks import calculate_user_streak_summary

create_goals_table()
create_calendar_table()

# Use a fresh user + specific goal records to validate the feature logic.
conn = sqlite3.connect("database.db")
conn.execute("DELETE FROM users WHERE username = 'smokeuser'")
conn.execute("DELETE FROM goals WHERE user_id IN (SELECT id FROM users WHERE username = 'smokeuser')")
conn.close()

user_id = signup("smokeuser", "password123")
add_goal(user_id, "water", "Drink water", 8, "glasses", "daily")
add_goal(user_id, "sleep", "Sleep well", 8, "hours", "daily")

# Day-level values are created from the health table.
conn = sqlite3.connect("database.db")
conn.execute(
    "INSERT INTO health(user_id, recorded_at, weight, water, sleep, exercise) VALUES (?, ?, ?, ?, ?, ?)",
    (user_id, "2026-09-10T08:00:00+00:00", 70.0, 8, 8.0, "30 minutes"),
)
conn.commit()
conn.close()

goals = get_goals_for_user(user_id)
summary = calculate_user_streak_summary(user_id)
calendar = get_calendar_month(user_id, 2026, 9)

assert len(goals) >= 2
assert summary["current_streak"] >= 0
assert isinstance(calendar["days"], list)
assert any(day["date"] == "2026-09-10" for day in calendar["days"])
print("feature smoke test ok")
