import os
import subprocess
import requests
import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv
from paths import get_data_path


def check_brain_setup():
    """Проверяет наличие API-ключа или локальной Ollama."""

    # 1. Проверяем, есть ли API-ключ
    env_path = get_data_path(".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    claude_key = os.getenv("CLAUDE_API_KEY", "").strip()

    # Если есть хоть какой-то ключ (и это не "ollama"), значит пользователь настроил API
    if (api_key and api_key.lower() != "ollama") or claude_key:
        return True

        # 2. Если ключа нет — проверяем Ollama
    print("[Setup] API-ключ не найден. Проверяем локальную Ollama...")

    try:
        # Стучимся в локальный API Ollama
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m['name'] for m in response.json().get('models', [])]

        if 'qwen2.5:7b' not in models:
            # Ollama есть, но модели нет
            ask_download_model()
            return False
        else:
            # Всё отлично, модель есть
            print("[Setup] Ollama и модель qwen2.5:7b найдены. Запускаем Дэна.")
            return True

    except requests.exceptions.ConnectionError:
        # Ollama вообще не установлена или не запущена
        show_ollama_install_window()
        return False


def show_ollama_install_window():
    """Окно с требованием установить Ollama."""
    root = ctk.CTk()
    root.title("Установка Дэна")
    root.geometry("500x300")

    ctk.CTkLabel(root, text="Требуется установка локального ИИ", font=("Arial", 18, "bold")).pack(pady=(20, 10))

    text = ("У вас не найден API-ключ (Claude/DeepSeek).\n"
            "Чтобы Дэн работал бесплатно, ему нужна программа Ollama.\n\n"
            "1. Скачайте и установите Ollama с официального сайта.\n"
            "2. После установки запустите Дэна заново.")

    ctk.CTkLabel(root, text=text, justify="left", font=("Arial", 13)).pack(pady=10, padx=20)

    def open_site():
        import webbrowser
        webbrowser.open("https://ollama.com/download")

    ctk.CTkButton(root, text="Скачать Ollama (откроется сайт)", command=open_site, height=40).pack(pady=10)
    ctk.CTkButton(root, text="Закрыть", fg_color="gray", command=root.destroy).pack()

    root.mainloop()


def ask_download_model():
    """Предлагает скачать модель, если Ollama есть, а модели нет."""
    root = ctk.CTk()
    root.title("Загрузка модели")
    root.geometry("500x250")

    ctk.CTkLabel(root, text="Нужна модель Qwen 2.5", font=("Arial", 18, "bold")).pack(pady=(20, 10))

    text = ("Ollama установлена, но нужной модели (qwen2.5:7b) нет.\n"
            "Нажмите кнопку ниже, чтобы скачать её (весит около 4.5 ГБ).\n"
            "Это может занять несколько минут.")

    ctk.CTkLabel(root, text=text, justify="center", font=("Arial", 13)).pack(pady=10)

    def download():
        # Запускаем скачивание в отдельном процессе, чтобы окно не зависло
        subprocess.Popen(["ollama", "pull", "qwen2.5:7b"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        messagebox.showinfo("Загрузка",
                            "Загрузка модели запущена в отдельном окне. Дождитесь окончания и запустите Дэна заново.")
        root.destroy()

    ctk.CTkButton(root, text="Скачать модель", command=download, height=40, fg_color="green",
                  hover_color="darkgreen").pack(pady=10)
    ctk.CTkButton(root, text="Отмена", fg_color="gray", command=root.destroy).pack()

    root.mainloop()