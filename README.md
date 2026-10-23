<div align="center">
  <img src="https://github.com/LazyFoxGame.png" width="150" style="border-radius: 50%;" />
  <h1>Den AI Assistant 🦊</h1>
  <p><b>Your personal, private, and free AI assistant for Windows.</b></p>
</div>

---

**Den** — это персональный голосовой ассистент, разработанный студией **Lazy Fox Games**. Он работает локально на вашем ПК, не требует платных подписок (если использовать локальный ИИ) и умеет выполнять реальные действия.

## 🚀 Features
*   **Voice Control:** Wake word "Den" and full text-to-speech via Piper.
*   **App Launcher:** Opens any application or Steam game by voice/text.
*   **Smart Search:** Fast file search using a local SQLite index.
*   **Memory:** Remembers facts about you and keeps chat history.
*   **Dual-Brain:** 
    *   **Free:** Works out-of-the-box with local Ollama models (Qwen 2.5).
    *   **Pro:** Connect your own Claude/DeepSeek API key for maximum intelligence.

## 🛠️ Tech Stack
*   Python 3.10+
*   CustomTkinter (GUI)
*   Ollama (Local LLM)
*   Piper (Local TTS)
*   SQLite (Memory & Index)

## 📦 Installation
1. Install [Python](https://www.python.org/) and [Ollama](https://ollama.com/).
2. Download the local AI model: `ollama pull qwen2.5:7b`
3. Clone the repository: `git clone https://github.com/LazyFoxGame/Den-AI-Assistant.git`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the assistant: `python main.py`

## 📫 Connect
*   Telegram channel: [@LazyFoxGames](https://t.me/LazyFoxGames)
