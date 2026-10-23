"""
llm.py — мозг Дэна.
Поддерживает два режима: DeepSeek (бесплатный) и Claude (Pro).
"""

import os
import json
import re
import datetime
from dotenv import load_dotenv
from openai import OpenAI

import config
import memory
import actions
import search
from paths import get_data_path

# Загружаем ключи из папки AppData
load_dotenv(get_data_path(".env"))


# --- Двойной мозг ---
def get_llm_client():
    """Выбирает мозг: Claude (если включен Pro) или DeepSeek (по умолчанию)."""
    cfg = config.load_config()

    if cfg.get("use_pro_brain", False):
        api_key = os.getenv("CLAUDE_API_KEY", "").strip()
        base_url = os.getenv("CLAUDE_BASE_URL", "").strip()
        model = os.getenv("CLAUDE_MODEL", "").strip()
        if api_key:
            return OpenAI(api_key=api_key, base_url=base_url), model
        else:
            print("[LLM] Включен Pro-режим, но нет ключа Claude. Откат на DeepSeek.")

    # По умолчанию DeepSeek
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "").strip()
    model = os.getenv("DEEPSEEK_MODEL", "").strip()
    return OpenAI(api_key=api_key, base_url=base_url), model


# --- Системный промпт ---
def build_system_prompt() -> str:
    """Собирает промпт из: строгих правил + имени пользователя + фактов."""
    cfg = config.load_config()

    prompt = config.BASE_RULES

    user_name = cfg.get("user_name", "друг")
    prompt += f"Обращайся к пользователю по имени: {user_name}.\n\n"

    facts = memory.facts_as_text()
    if facts:
        prompt += facts + "\n"

    return prompt


# --- Инструменты ---
TOOLS = [
    {"type": "function", "function": {"name": "system_info", "description": "Получить загрузку CPU, RAM и диска C.",
                                      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "list_files", "description": "Показать содержимое папки.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                                                     "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_text_file", "description": "Прочитать текстовый файл.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                                                     "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_text_file", "description": "Записать текст в файл.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"},
                                                                                      "content": {"type": "string"}},
                                                     "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "launch_app", "description": "Запустить программу или игру по названию.",
                                      "parameters": {"type": "object", "properties": {"command": {"type": "string"}},
                                                     "required": ["command"]}}},
    {"type": "function", "function": {"name": "find_file", "description": "Найти файл по имени в стандартных папках.",
                                      "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                                                     "required": ["query"]}}},
    {"type": "function", "function": {"name": "run_powershell", "description": "Выполнить команду PowerShell.",
                                      "parameters": {"type": "object", "properties": {"command": {"type": "string"}},
                                                     "required": ["command"]}}},
    {"type": "function", "function": {"name": "save_fact", "description": "Сохранить важный факт о пользователе.",
                                      "parameters": {"type": "object", "properties": {"key": {"type": "string"},
                                                                                      "value": {"type": "string"}},
                                                     "required": ["key", "value"]}}},
]


def _call_tool(name: str, args: dict) -> str:
    """Вызывает нужный инструмент по имени."""
    if name in actions.ACTIONS:
        fn = actions.ACTIONS[name]
        return fn(**args) if args else fn()
    if name == "launch_app":
        return search.launch_app(args.get("command", ""))
    if name == "find_file":
        return search.find_file(args.get("query", ""))
    if name == "save_fact":
        return memory.save_fact(args.get("key", ""), args.get("value", ""))
    return f"Неизвестный инструмент: {name}"


# --- Роутер простых команд (без ИИ) ---
SIMPLE_PATTERNS = [
    (re.compile(r"^(открой|запусти|включи|открыть|запустить)\s+(.+)$", re.IGNORECASE),
     lambda m: search.launch_app(m.group(2).strip())),
    (re.compile(r"^котор(ый|ое)\s+час", re.IGNORECASE),
     lambda m: f"Сейчас {datetime.datetime.now().strftime('%H:%M')}"),
    (re.compile(r"^какой\s+сегодня\s+день", re.IGNORECASE),
     lambda m: f"Сегодня {datetime.datetime.now().strftime('%d.%m.%Y')}"),
]


def try_simple_route(text: str):
    """Пытается обработать команду без ИИ."""
    text = text.strip()
    for pattern, handler in SIMPLE_PATTERNS:
        m = pattern.match(text)
        if m:
            try:
                return handler(m)
            except Exception:
                return None
    return None


# --- Основная функция ---
def ask(user_text: str, max_iterations: int = 12) -> str:
    """Отправляет запрос в выбранный ИИ (DeepSeek или Claude)."""

    # 1. Пробуем простой роутер (мимо ИИ)
    simple = try_simple_route(user_text)
    if simple is not None:
        memory.save_message("user", user_text)
        memory.save_message("assistant", simple)
        return simple

    # 2. Собираем контекст
    messages = [{"role": "system", "content": build_system_prompt()}]
    messages += memory.load_recent_messages(limit=15)
    messages.append({"role": "user", "content": user_text})

    # Получаем нужный клиент (DeepSeek или Claude)
    client, model_name = get_llm_client()

    # 3. Цикл вызова инструментов
    for _ in range(max_iterations):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            return f"Ошибка связи с ИИ: {e}"

        msg = response.choices[0].message

        # Если нет вызовов инструментов — это финальный текстовый ответ
        if not msg.tool_calls:
            answer = msg.content or "…"
            memory.save_message("user", user_text)
            memory.save_message("assistant", answer)
            return answer

        # Добавляем ответ ассистента (с вызовом инструментов) в историю
        messages.append(msg.model_dump(exclude_none=True))

        # Выполняем каждый вызов
        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            try:
                result = _call_tool(name, args)
            except Exception as e:
                result = f"Ошибка инструмента {name}: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })

    return "Слишком много шагов подряд. Попробуй переформулировать."