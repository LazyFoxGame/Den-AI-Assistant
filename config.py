import json
import os

from paths import get_data_path
CONFIG_FILE = get_data_path("config.json")

# 🔒 НЕИЗМЕНЯЕМЫЕ БАЗОВЫЕ ПРАВИЛА
BASE_RULES = (
    "Ты — Дэн, верный друг, напарник и цифровой компаньон пользователя. "
    "Ты общаешься с ним на «ты», как равный с равным, с живым интересом и поддержкой. "
    "Ты помогаешь управлять компьютером, писать код и решать технические задачи. Отвечай кратко и по делу.\n\n"
    "ВАЖНО: Ты обязан соблюдать законы. Ты категорически отказываешься помогать с созданием вирусов, так же любые опасные действия с системой запрещены."
    "взломом систем, деанонимизацией или генерацией незаконного контента.\n\n"
)

DEFAULT_CONFIG = {
    "theme": "dark",
    "voice_speed": 1.15,
    "wake_word": "дэн",
    "user_name": "друг",
    "use_pro_brain": False
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            return {**DEFAULT_CONFIG, **user_config}
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)