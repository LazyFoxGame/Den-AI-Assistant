"""
memory.py — память Дэна.

Два уровня:
1. История сообщений (что было в диалоге) — последние N штук идут в контекст.
2. Факты (устойчивые знания о пользователе) — "меня зовут X", "браузер — Firefox".
"""

import sqlite3
from datetime import datetime


from paths import get_data_path
DB = get_data_path("dan_memory.db")

def init_db() -> None:
    """Создаёт таблицы, если их нет. Вызывать при старте."""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_message(role: str, content: str) -> None:
    """Сохраняет сообщение в историю."""
    if not content:
        return
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO messages (role, content) VALUES (?, ?)",
        (role, content)
    )
    conn.commit()
    conn.close()


def load_recent_messages(limit: int = 15) -> list:
    """Возвращает последние N сообщений в формате для Claude."""
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    # Разворачиваем, чтобы старые шли первыми
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def clear_history() -> None:
    """Очищает историю (полезно для тестов)."""
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()


def save_fact(key: str, value: str) -> str:
    """Сохраняет факт о пользователе. Если ключ есть — обновляет."""
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR REPLACE INTO facts (key, value, ts) VALUES (?, ?, ?)",
        (key.lower().strip(), value.strip(), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return f"Запомнил: {key} = {value}"


def get_all_facts() -> dict:
    """Возвращает все факты в виде словаря."""
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT key, value FROM facts").fetchall()
    conn.close()
    return {k: v for k, v in rows}


def facts_as_text() -> str:
    """Возвращает факты одной строкой для вставки в системный промпт."""
    facts = get_all_facts()
    if not facts:
        return ""
    lines = [f"- {k}: {v}" for k, v in facts.items()]
    return "Что я знаю о пользователе:\n" + "\n".join(lines)


def forget_fact(key: str) -> str:
    """Удаляет факт."""
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM facts WHERE key = ?", (key.lower().strip(),))
    conn.commit()
    conn.close()
    return f"Забыл: {key}"