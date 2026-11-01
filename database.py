import sqlite3
from datetime import datetime

DB_NAME = "chat_history.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            pdf_name TEXT,
            pdf_text TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        )
    """)
    cursor.execute("PRAGMA table_info(chats)")
    columns=[column[1] for column in cursor.fetchall()]
   
   
    if"pdf_name" not in columns:
        cursor.execute("ALTER TABLE chats ADD COLUMN pdf_name TEXT")
    if"pdf_text" not in columns:
        cursor.execute("ALTER TABLE chats ADD COLUMN pdf_text TEXT")
    conn.commit()
    conn.close()


def create_chat(title="New Chat",pdf_name="Unknown PDF",pdf_text=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chats (title, pdf_name, pdf_text, created_at) VALUES (?,?,?,?)",
        (title,pdf_name, pdf_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    chat_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return chat_id


def save_message(chat_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, role, content)
    )

    conn.commit()
    conn.close()


def get_all_chats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, pdf_name, pdf_text, created_at FROM chats ORDER BY id DESC"
    )

    chats = cursor.fetchall()
    conn.close()

    return chats


def get_chat_messages(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id",
        (chat_id,)
    )

    messages = cursor.fetchall()
    conn.close()

    return messages


def delete_chat(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM messages WHERE chat_id = ?", (chat_id,)
    )

    cursor.execute(
        "DELETE FROM chats WHERE id = ?", (chat_id,)
    )

    conn.commit()
    conn.close()