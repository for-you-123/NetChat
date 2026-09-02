import sqlite3
from datetime import datetime
from chat_common.config import DATABASE_FILE
def init_database():
    db_conn = sqlite3.connect(
        DATABASE_FILE,
        timeout=5
    )
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT NOT NULL,
                target TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        db_conn.commit()
    finally:
        db_conn.close()
def save_message(
    username,
    content,
    message_type="message",
    target=None
):
    db_conn = sqlite3.connect(
        DATABASE_FILE,
        timeout=5
    )
    try:
        cursor = db_conn.cursor()
        created_at = (
            datetime.now()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
        cursor.execute(
            """
            INSERT INTO messages (
                username,
                content,
                message_type,
                target,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                username,
                content,
                message_type,
                target,
                created_at
            )
        )
        db_conn.commit()
        return created_at
    finally:
        db_conn.close()
def load_messages():
    db_conn = sqlite3.connect(
        DATABASE_FILE,
        timeout=5
    )
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                username,
                content,
                message_type,
                target,
                created_at
            FROM messages
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()
        return rows
    finally:
        db_conn.close()