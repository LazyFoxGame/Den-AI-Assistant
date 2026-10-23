"""
search.py — поиск приложений и файлов для Дэна.
Индекс строится один раз, поиск идёт по SQLite — мгновенно.
Steam-игры запускаются через протокол steam://rungameid/.
"""

import os
import sqlite3
import json
import subprocess
from pathlib import Path

from paths import get_data_path
INDEX_DB = get_data_path("dan_index.db")


SYNONYMS = {
    "стим": "steam",
    "дискорд": "discord",
    "хром": "chrome",
    "телеграм": "telegram",
    "телега": "telegram",
    "блокнот": "notepad",
    "калькулятор": "calc",
    "ворд": "word",
    "эксель": "excel",
    "опера": "opera",
    "фаерфокс": "firefox",
    "файрфокс": "firefox",
    "зум": "zoom",
    "скайп": "skype",
    "спотифай": "spotify",
}


# Steam AppID популярных игр
STEAM_GAMES = {
    "кс2": "730", "кс": "730", "cs2": "730", "cs 2": "730",
    "counter-strike 2": "730", "counter strike 2": "730",
    "кс го": "730", "cs go": "730", "ксго": "730",
    "дота": "570", "дота 2": "570", "dota": "570", "dota 2": "570",
    "гта 5": "271590", "gta 5": "271590", "gta v": "271590", "гта5": "271590",
    "пабг": "578080", "pubg": "578080",
    "раст": "252490", "rust": "252490",
    "тим фортресс 2": "440", "tf2": "440",
    "террария": "105600", "terraria": "105600",
}


def _clean_query(query: str) -> str:
    """Убирает префиксы и заменяет синонимы."""
    if not query:
        return ""
    query = query.lower().strip()
    for prefix in ["запусти", "открой", "включи", "найди и запусти",
                   "найди", "приложение", "игру", "программу"]:
        query = query.replace(prefix, "").strip()
    for ru, en in SYNONYMS.items():
        if ru in query:
            query = query.replace(ru, en).strip()
            break
    return query


def build_app_index(verbose: bool = True) -> int:
    """Строит индекс приложений ОДИН РАЗ."""
    conn = sqlite3.connect(INDEX_DB)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS apps")
    c.execute("CREATE TABLE apps (name TEXT, path TEXT, source TEXT)")
    c.execute("CREATE INDEX idx_name ON apps(name)")

    search_dirs = [
        Path(os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs")),
        Path(os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs")),
        Path(os.path.expandvars(r"%UserProfile%\Desktop")),
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
        Path(os.path.expandvars(r"%LocalAppData%\Programs")),
        Path(r"C:\Windows\System32"),
    ]

    seen = set()
    count = 0

    for base in search_dirs:
        if not base.exists():
            continue
        for ext in ("*.lnk", "*.exe"):
            try:
                for p in base.rglob(ext):
                    name = p.stem.lower()
                    if name in seen:
                        continue
                    seen.add(name)
                    c.execute("INSERT INTO apps VALUES (?, ?, ?)",
                              (name, str(p), str(base)))
                    count += 1
            except (PermissionError, OSError):
                continue

    conn.commit()
    conn.close()

    if verbose:
        print(f"[Index] Готово. Записей: {count}")
    return count


def ensure_index() -> None:
    """Проверяет, есть ли индекс. Если нет — строит."""
    if not os.path.exists(INDEX_DB):
        print("[Index] Индекса нет, строю...")
        build_app_index()
        return
    try:
        conn = sqlite3.connect(INDEX_DB)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM apps")
        n = c.fetchone()[0]
        conn.close()
        if n == 0:
            print("[Index] Индекс пуст, перестраиваю...")
            build_app_index()
    except sqlite3.Error:
        print("[Index] База повреждена, перестраиваю...")
        build_app_index()


def find_app(query: str):
    """Ищет приложение по индексу. Мгновенно."""
    q = _clean_query(query)
    if not q:
        return None

    conn = sqlite3.connect(INDEX_DB)
    c = conn.cursor()
    c.execute("SELECT path FROM apps WHERE name = ? LIMIT 1", (q,))
    row = c.fetchone()
    if row:
        conn.close()
        return row[0]

    c.execute("SELECT path, name FROM apps WHERE name LIKE ? LIMIT 10",
              (f"{q}%",))
    rows = c.fetchall()
    if len(rows) == 1:
        conn.close()
        return rows[0][0]

    if not rows:
        c.execute("SELECT path, name FROM apps WHERE name LIKE ? LIMIT 10",
                  (f"%{q}%",))
        rows = c.fetchall()

    conn.close()

    if len(rows) == 1:
        return rows[0][0]
    if rows:
        return {"multiple": [{"name": r[1], "path": r[0]} for r in rows]}
    return None


def launch_steam_game(query: str):
    """Запускает игру через Steam по AppID. Возвращает текст или None."""
    q = query.lower().strip()
    game_id = STEAM_GAMES.get(q)
    if not game_id:
        return None
    try:
        os.startfile(f"steam://rungameid/{game_id}")
        return f"Запускаю через Steam: {query}"
    except Exception as e:
        return f"Не удалось запустить Steam-игру: {e}"


def launch_app(query: str) -> str:
    """Запускает приложение. Сначала Steam, потом обычный поиск."""
    cleaned = _clean_query(query)

    # 1. Steam-игра?
    steam = launch_steam_game(cleaned)
    if steam:
        return steam

    # 2. Обычный поиск
    target = find_app(query)

    if target is None:
        return f"Не нашёл приложение '{query}'. Попробуй уточнить название."

    if isinstance(target, dict):
        names = ", ".join(item["name"] for item in target["multiple"][:5])
        return f"Нашёл несколько вариантов: {names}. Уточни, какое открыть."

    try:
        if target.lower().endswith(".lnk"):
            os.startfile(target)
        elif target.lower().endswith(".exe"):
            creation = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            subprocess.Popen([target], creationflags=creation)
        else:
            os.startfile(target)
        return f"Открыл: {Path(target).stem}"
    except Exception as e:
        return f"Не удалось открыть '{query}': {e}"


def find_file(query: str, search_dirs=None, limit: int = 10) -> str:
    """Ищет файл по имени в стандартных папках."""
    if search_dirs is None:
        search_dirs = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
        ]

    q = query.lower().strip()
    results = []

    for base in search_dirs:
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if p.is_file() and q in p.name.lower():
                    results.append({
                        "name": p.name,
                        "path": str(p),
                        "size_kb": round(p.stat().st_size / 1024, 1),
                    })
                    if len(results) >= limit:
                        break
        except (PermissionError, OSError):
            continue
        if len(results) >= limit:
            break

    if not results:
        return json.dumps({"found": 0, "message": f"Файл '{query}' не найден."},
                          ensure_ascii=False)
    return json.dumps({"found": len(results), "files": results},
                      ensure_ascii=False, indent=2)