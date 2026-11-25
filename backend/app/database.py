import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.config import settings

def get_db_path() -> str:
    url = settings.DATABASE_URL
    if url.startswith("sqlite:////"):
        # Unix root-relative absolute path e.g. sqlite:////data/app.db -> /data/app.db
        path = "/" + url[len("sqlite:////"):]
    elif url.startswith("sqlite:///"):
        path = url[len("sqlite:///"):]
    elif url.startswith("sqlite://"):
        path = url[len("sqlite://"):]
    else:
        path = url
    return path

def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    parent_dir = os.path.dirname(os.path.abspath(db_path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
        
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);
            """)
    finally:
        conn.close()

def check_db_health() -> bool:
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            return result is not None and result[0] == 1
        finally:
            conn.close()
    except Exception:
        return False

def get_session_messages(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Returns list of stored messages for a session ordered oldest first.
    If session doesn't exist (no messages), returns None so 404 can be returned.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, metadata FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        
        result = []
        for r in rows:
            item: Dict[str, Any] = {
                "role": r["role"],
                "content": r["content"],
            }
            if r["role"] == "assistant" and r["metadata"]:
                try:
                    item["metadata"] = json.loads(r["metadata"])
                except Exception:
                    item["metadata"] = {}
            result.append(item)
        return result
    finally:
        conn.close()

def save_interaction(
    session_id: str,
    user_content: str,
    assistant_content: str,
    assistant_metadata: Dict[str, Any]
):
    """
    Atomically saves both the user message and the assistant message in SQLite.
    Timestamp is ISO-8601 server time.
    """
    conn = get_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(assistant_metadata)
        with conn:
            # Insert user message
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, metadata, created_at)
                VALUES (?, 'user', ?, NULL, ?)
                """,
                (session_id, user_content, now_iso)
            )
            # Insert assistant message
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, metadata, created_at)
                VALUES (?, 'assistant', ?, ?, ?)
                """,
                (session_id, assistant_content, metadata_json, now_iso)
            )
    finally:
        conn.close()
