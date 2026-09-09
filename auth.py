import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path


def _resolve_db_path():
    db_path = Path(os.getenv("HEALTH_DB_PATH", Path(__file__).resolve().parent / "database.db"))
    db_path = db_path.expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


DB_PATH = _resolve_db_path()
HASH_ITERATIONS = 600_000


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password, stored_hash):
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def create_users_table():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT
            )
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)")
        }
        if "password_hash" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            columns.add("password_hash")
        if "password" in columns:
            legacy_users = connection.execute(
                "SELECT id, password FROM users WHERE password_hash IS NULL AND password IS NOT NULL"
            ).fetchall()
            for user in legacy_users:
                connection.execute(
                    "UPDATE users SET password_hash = ?, password = NULL WHERE id = ?",
                    (_hash_password(user["password"]), user["id"]),
                )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )


def signup(username, password):
    username = username.strip()
    if len(username) < 3 or len(password) < 8:
        raise ValueError("Username must have 3+ characters and password 8+ characters.")
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            (username, _hash_password(password)),
        )
        return cursor.lastrowid


def login(username, password):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
    if user and _verify_password(password, user["password_hash"]):
        return {"id": user["id"], "username": user["username"]}
    return None


create_users_table()