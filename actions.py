"""
actions.py — действия, которые Дэн может выполнять на ПК.
Всё, что не поиск и не память: система, файлы, PowerShell.
"""

import os
import json
import subprocess
from pathlib import Path

import psutil


# --- Заблокированные команды PowerShell ---
DANGEROUS = (
    "remove-item", "del ", "erase ", "format-", "clear-disk",
    "stop-computer", "restart-computer", "shutdown", "reg delete",
    "set-executionpolicy", "irm ", "iex ", "invoke-expression",
    "net user", "net localgroup", "icacls", "takeown",
    "rm -rf", "rmdir /s",
)


def system_info() -> str:
    """Загрузка CPU, RAM, диска C."""
    try:
        return json.dumps({
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_total_gb": round(psutil.virtual_memory().total / 2 ** 30, 1),
            "disk_c_percent": psutil.disk_usage("C:\\").percent,
        }, ensure_ascii=False)
    except Exception as e:
        return f"Ошибка получения системной информации: {e}"


def list_files(path: str) -> str:
    """Показать содержимое папки."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"Путь не существует: {p}"
    if not p.is_dir():
        return f"Это не папка: {p}"

    out = []
    for x in p.iterdir():
        try:
            item = {
                "name": x.name,
                "type": "folder" if x.is_dir() else "file",
            }
            if x.is_file():
                item["size_mb"] = round(x.stat().st_size / 2 ** 20, 2)
            out.append(item)
        except OSError:
            pass

    if not out:
        return f"Папка пуста: {p}"
    return json.dumps(out[:200], ensure_ascii=False, indent=2)


def read_text_file(path: str) -> str:
    """Прочитать текстовый файл."""
    p = Path(path).expanduser()
    if not p.is_file():
        return f"Файл не найден: {p}"
    if p.stat().st_size > 2_000_000:
        return "Файл слишком большой (больше 2 МБ)."
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Ошибка чтения: {e}"


def write_text_file(path: str, content: str) -> str:
    """Записать текст в файл."""
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Файл записан: {p}"
    except Exception as e:
        return f"Ошибка записи: {e}"


def run_powershell(command: str) -> str:
    """Выполнить PowerShell с защитой от опасных команд."""
    cmd_lower = command.lower()
    for danger in DANGEROUS:
        if danger in cmd_lower:
            return f"Операция заблокирована протоколом безопасности Дэна (найдено: '{danger}')."

    try:
        creation = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=30,
            creationflags=creation,
        )
        return json.dumps({
            "returncode": r.returncode,
            "stdout": r.stdout[-6000:],
            "stderr": r.stderr[-6000:],
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return "Команда выполнялась слишком долго (больше 30 секунд)."
    except Exception as e:
        return f"Ошибка выполнения команды: {e}"


# --- Реестр действий: имя → функция ---
ACTIONS = {
    "system_info": system_info,
    "list_files": list_files,
    "read_text_file": read_text_file,
    "write_text_file": write_text_file,
    "run_powershell": run_powershell,
}