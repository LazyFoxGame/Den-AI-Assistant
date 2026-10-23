"""
gui.py — графический интерфейс Дэна.
GUI не знает, как работает LLM — он просто вызывает llm.ask() в фоне.
"""

import threading
import config

import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw

import llm
import voice


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class DenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Дэн — Персональный Ассистент")
        self.geometry("800x580")
        self.minsize(650, 450)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.voice_mode = ctk.StringVar(value="off")
        self.den_voice = None
        self.wake_listener = None
        self.tray_icon = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Шапка ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.header_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(15, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame, text="🦊 Дэн AI",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        # Кнопка настроек (шестеренка)
        self.settings_btn = ctk.CTkButton(
            self.header_frame, text="⚙️", width=40, height=28,
            fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), command=self.open_settings
        )
        self.settings_btn.grid(row=0, column=1, padx=10, sticky="e")

        self.voice_switch = ctk.CTkSwitch(
            self.header_frame, text="Слушать «Дэн»",
            command=self.toggle_voice_mode, variable=self.voice_mode,
            onvalue="wake_word", offvalue="off",
            font=ctk.CTkFont(family="Arial", size=13),
        )
        self.voice_switch.grid(row=0, column=2, sticky="e")

        # --- Чат ---
        self.chat_container = ctk.CTkFrame(self, corner_radius=12)
        self.chat_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.chat_container.grid_rowconfigure(0, weight=1)
        self.chat_container.grid_columnconfigure(0, weight=1)

        self.chat_box = ctk.CTkTextbox(
            self.chat_container, wrap="word",
            font=ctk.CTkFont(family="Arial", size=14),
            fg_color="transparent", border_width=0,
        )
        self.chat_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_box.configure(state="disabled")

        # --- Панель ввода ---
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent", height=70)
        self.input_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(5, 20))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Введите сообщение или задачу для Дэна...",
            font=ctk.CTkFont(family="Arial", size=14),
            height=45, corner_radius=10,
        )
        self.entry.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.send_btn = ctk.CTkButton(
            self.input_frame, text="Отправить",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            width=110, height=45, corner_radius=10, command=self.send_message,
        )
        self.send_btn.grid(row=0, column=1, sticky="e")

        self.append_chat("Система", "Окно запущено. Инициализирую голосовой движок в фоне...")
        threading.Thread(target=self.init_voice_engine, daemon=True).start()

    # --- Инициализация голоса ---
    def init_voice_engine(self):
        try:
            self.den_voice = voice.DenVoice()
            hello = "Привет. Дэн на связи. Какую задачу сегодня решим?"
            self.append_chat("Дэн", hello)
            self.den_voice.say(hello)
        except Exception as e:
            self.append_chat("Система", f"Ошибка инициализации голоса: {e}")

    # --- Трей ---
    def create_tray_icon_image(self):
        image = Image.new("RGB", (64, 64), color=(33, 150, 243))
        dc = ImageDraw.Draw(image)
        dc.text((22, 18), "Д", fill=(255, 255, 255))
        return image

    def open_settings(self):
        cfg = config.load_config()

        settings_win = ctk.CTkToplevel(self)
        settings_win.title("Настройки Дэна")
        settings_win.geometry("450x450")  # Уменьшили высоту, так как настроек стало меньше
        settings_win.attributes("-topmost", True)
        settings_win.grab_set()

        # --- 1. Тема ---
        ctk.CTkLabel(settings_win, text="Тема интерфейса", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        theme_var = ctk.StringVar(value=cfg["theme"])
        theme_menu = ctk.CTkOptionMenu(settings_win, values=["dark", "light", "system"], variable=theme_var)
        theme_menu.pack(pady=5)

        # --- 2. Скорость голоса ---
        ctk.CTkLabel(settings_win, text="Скорость голоса (1.0 - быстро, 1.5 - медленно)",
                     font=("Arial", 14, "bold")).pack(pady=(15, 5))
        speed_var = ctk.DoubleVar(value=cfg["voice_speed"])
        speed_slider = ctk.CTkSlider(settings_win, from_=0.8, to=1.5, variable=speed_var, number_of_steps=14)
        speed_slider.pack(pady=5)
        speed_label = ctk.CTkLabel(settings_win, text=f"Текущая: {speed_var.get():.2f}")
        speed_label.pack()

        def update_speed_label(val):
            speed_label.configure(text=f"Текущая: {float(val):.2f}")

        speed_slider.configure(command=update_speed_label)

        # --- 3. Слово активации ---
        ctk.CTkLabel(settings_win, text="Слово активации", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        wake_entry = ctk.CTkEntry(settings_win, width=200)
        wake_entry.insert(0, cfg["wake_word"])
        wake_entry.pack(pady=5)

        # --- 4. Имя пользователя ---
        ctk.CTkLabel(settings_win, text="Твое имя (как обращаться)", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        name_entry = ctk.CTkEntry(settings_win, width=200)
        name_entry.insert(0, cfg["user_name"])
        name_entry.pack(pady=5)

        # --- Кнопка сохранения ---
        def save_and_close():
            new_cfg = {
                "theme": theme_var.get(),
                "voice_speed": round(speed_var.get(), 2),
                "wake_word": wake_entry.get().strip().lower() or "дэн",
                "user_name": name_entry.get().strip() or "друг"
            }
            config.save_config(new_cfg)

            ctk.set_appearance_mode(new_cfg["theme"])

            self.append_chat("Система", "✅ Настройки сохранены.")
            settings_win.destroy()

        save_btn = ctk.CTkButton(settings_win, text="Сохранить", command=save_and_close, fg_color="green",
                                 hover_color="darkgreen", height=40)
        save_btn.pack(pady=25, fill="x", padx=40)
    def hide_to_tray(self):
        self.withdraw()
        try:
            image = self.create_tray_icon_image()
            menu = pystray.Menu(
                pystray.MenuItem("Открыть Дэна", self.show_from_tray, default=True),
                pystray.MenuItem("Выход", self.exit_from_tray),
            )
            self.tray_icon = pystray.Icon("DenAssistant", image, "Дэн — Ассистент", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"[Tray Error]: {e}")
            self.deiconify()

    def show_from_tray(self, icon, item):
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.deiconify()

    def exit_from_tray(self, icon, item):
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.destroy()

    # --- Чат ---
    def append_chat(self, sender, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"\n{sender}: {text}\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def send_message(self):
        user_text = self.entry.get().strip()
        if not user_text:
            return
        self.entry.delete(0, "end")
        self.append_chat("Ты", user_text)
        threading.Thread(
            target=self.process_ai_response,
            args=(user_text,),
            daemon=True,
        ).start()

    def process_ai_response(self, user_text):
        try:
            answer = llm.ask(user_text)
        except Exception as e:
            answer = f"Ошибка: {e}"
        self.append_chat("Дэн", answer)
        if self.den_voice:
            self.den_voice.say(answer)

    # --- Wake word ---
    def toggle_voice_mode(self):
        mode = self.voice_mode.get()
        if mode == "wake_word":
            self.append_chat("Система", "🎙️ Режим активации по слову «Дэн» включен.")
            if self.wake_listener is None:
                self.wake_listener = voice.WakeWordListener(self.on_wake_word)
            self.wake_listener.start()
        else:
            self.append_chat("Система", "🔇 Голосовое прослушивание выключено.")
            if self.wake_listener:
                self.wake_listener.stop()

    def on_wake_word(self, recognized_text: str):
        """Вызывается из WakeWordListener, когда услышали «Дэн»."""
        self.append_chat("Система", f"🎯 Услышано: '{recognized_text}'")
        self.entry.delete(0, "end")
        self.entry.insert(0, recognized_text)
        self.send_message()