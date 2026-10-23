import search
import memory
import gui
import setup_brain

def main():
    print("[Den] Запуск...")

    # 1. Проверяем мозг (есть ли ключ или Ollama)
    if not setup_brain.check_brain_setup():
        print("[Den] Настройка не завершена. Выход.")
        return

    # 2. Индекс приложений
    search.ensure_index()

    # 3. Память
    memory.init_db()

    # 4. GUI
    app = gui.DenApp()
    app.mainloop()

if __name__ == "__main__":
    main()