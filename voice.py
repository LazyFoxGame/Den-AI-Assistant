import os
import re
import sys
import queue
import threading
import subprocess
import time as _time

import pygame
import speech_recognition as sr


class DenVoice:
    """Голосовой движок Дэна на Piper (безопасный, локальный)."""

    def __init__(self, model_name: str = "ru_RU-dmitri-medium.onnx", **kwargs):
        if getattr(sys, "frozen", False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # В режиме .exe модель лежит в _internal
        from paths import get_resource_path
        self.model_path = get_resource_path(model_name)
        self.base_dir_abs = self.base_dir

        self._queue = queue.Queue()
        self._shutdown = threading.Event()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()
        print(f"[Voice] Piper готов. Модель: {self.model_path}")

    def say(self, text: str) -> None:
        if text and text.strip():
            self._queue.put(text)

    def stop(self) -> None:
        self._shutdown.set()

    def _run(self) -> None:
        while not self._shutdown.is_set():
            try:
                text = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self._speak(text)
            except Exception as e:
                print(f"[Voice] Ошибка синтеза: {e}")
            finally:
                self._queue.task_done()

    def _speak(self, text: str) -> None:
        clean = self._clean_text_for_speech(text)
        if not clean:
            return
        self._speak_with_piper(clean)

    def _clean_text_for_speech(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"[*_#`~\[\]()|\\>+=]", " ", text)
        emoji_pattern = re.compile(
            "[" "\U0001f000-\U0001faff" "\U00002700-\U000027bf"
            "\U0001f900-\U0001f9ff" "\U0001fa70-\U0001faff" "]+",
            flags=re.UNICODE,
        )
        text = emoji_pattern.sub(r"", text)
        text = text.replace("Ден", "Дэн").replace("ден", "дэн")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _speak_with_piper(self, text: str) -> None:
        """Запускает Piper с настройками под 'дружелюбный' голос."""
        from paths import get_resource_path
        piper_path = get_resource_path(os.path.join("piper", "piper.exe"))

        output_audio = os.path.join(self.base_dir_abs, f"output_{int(_time.time() * 1000)}.wav")

        # length_scale=1.15 делает речь чуть медленнее и спокойнее
        # noise_scale=0.6 добавляет легкую "живую" вариативность интонации
        cmd = [
            piper_path,
            "--model", self.model_path,
            "--output_file", output_audio,
            "--length_scale", "1.15",
            "--noise_scale", "0.6"
        ]

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
            )
            stdout, stderr = process.communicate(input=text.encode("utf-8"))

            if os.path.exists(output_audio):
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(output_audio)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.unload()
                try:
                    os.remove(output_audio)
                except OSError:
                    pass
            else:
                print("Файл аудио не был создан!")

        except Exception as e:
            print(f"[Voice] Ошибка Piper: {e}")

class WakeWordListener:
                """Слушает микрофон в фоне. При слове «Дэн» вызывает callback."""

                def __init__(self, callback):
                    self.callback = callback
                    self.running = False
                    self._thread = None

                def start(self) -> None:
                    if self.running:
                        return
                    self.running = True
                    self._thread = threading.Thread(target=self._loop, daemon=True)
                    self._thread.start()

                def stop(self) -> None:
                    self.running = False

                def _loop(self) -> None:
                    recognizer = sr.Recognizer()
                    while self.running:
                        try:
                            with sr.Microphone() as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                                audio = recognizer.listen(source, timeout=4, phrase_time_limit=8)

                            text = recognizer.recognize_google(audio, language="ru-RU").lower()

                            if "дэн" in text or "ден" in text:
                                self.callback(text)
                        except sr.WaitTimeoutError:
                            continue
                        except Exception:
                            continue