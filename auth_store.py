from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


BASE_DIR = Path(__file__).resolve().parent
if os.getenv("VERCEL"):
    DEFAULT_DB_PATH = Path("/tmp/auth.db")
else:
    DEFAULT_DB_PATH = BASE_DIR / "auth.db"
DB_PATH = Path(os.getenv("AUTH_DB_PATH", str(DEFAULT_DB_PATH))).expanduser().resolve()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def fetch_user_by_email(email: str):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ? LIMIT 1",
            (email.strip(),),
        ).fetchone()


def fetch_user_by_id(user_id: int):
    try:
        normalized_id = int(user_id)
    except (TypeError, ValueError):
        return None

    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE id = ? LIMIT 1",
            (normalized_id,),
        ).fetchone()


def create_user(name: str, email: str, password_hash: str):
    timestamp = _utc_now()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name.strip(), email.strip(), password_hash, timestamp, timestamp),
        )
        conn.commit()
        return conn.execute(
            "SELECT * FROM users WHERE id = ? LIMIT 1",
            (cursor.lastrowid,),
        ).fetchone()
