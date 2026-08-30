import sqlite3
from datetime import datetime
DATABASE_FILE = "chatroom.db"
def init_database():
    """
    初始化数据库。

    如果 chatroom.db 不存在：
        SQLite 会自动创建。

    如果 messages 表不存在：
        创建 messages 表。
    """
    db_conn = sqlite3.connect(DATABASE_FILE)
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
    db_conn.close()
def save_message(
    username,
    content,
    message_type="message",
    target=None
):
    """
    保存一条聊天记录。

    username:
        谁发送的。

    content:
        消息正文。

    message_type:
        message = 群聊
        private = 私聊

    target:
        私聊目标。
        群聊时为 None。
    """
    db_conn = sqlite3.connect(DATABASE_FILE)
    cursor = db_conn.cursor()
    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
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
    db_conn.close()
def load_messages():
    db_conn = sqlite3.connect(DATABASE_FILE)
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
    db_conn.close()
    return rows