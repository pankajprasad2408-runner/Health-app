import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path


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


def create_health_table():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS health(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                recorded_at TEXT NOT NULL,
                weight REAL DEFAULT 0,
                water INTEGER DEFAULT 0,
                sleep REAL DEFAULT 0,
                exercise TEXT DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(health)")
        }
        if "user_id" not in columns:
            connection.execute("ALTER TABLE health ADD COLUMN user_id INTEGER")
        if "recorded_at" not in columns:
            connection.execute(
                "ALTER TABLE health ADD COLUMN recorded_at TEXT"
            )
            connection.execute(
                "UPDATE health SET recorded_at = ? WHERE recorded_at IS NULL",
                (datetime.now(timezone.utc).isoformat(),),
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_health_user_date ON health(user_id, recorded_at)"
        )


def add_health_data(user_id, weight, water, sleep, exercise, recorded_at=None):
    if not user_id:
        raise ValueError("A signed-in user is required.")
    if weight < 0 or water < 0 or not 0 <= sleep <= 24:
        raise ValueError("Health values are outside their valid ranges.")
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO health(user_id, recorded_at, weight, water, sleep, exercise)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, recorded_at, weight, water, sleep, exercise.strip()),
        )
        return cursor.lastrowid


create_health_table()