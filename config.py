"""RAGVA configuration.

All secrets come from environment variables. Never commit a real API key.

PowerShell example::

    $env:GROQ_API_KEY = "your-key-here"
    python ragva.py
"""

import os


# --- Assistant -------------------------------------------------------------
ASSISTANT_NAME = "RAGVA"
WAKE_WORD = "ragva"
LAUNCH_PHRASE = "ragva wake up"
CONTINUOUS_LISTEN = False
REQUIRE_WAKE_WORD = False

# --- Reasoning (Groq) ------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_HISTORY_TURNS = 20
SYSTEM_PROMPT = (
    "You are RAGVA, a concise voice-first desktop assistant. "
    "Use the available tools when they are needed, and keep spoken replies short."
)

# --- Speech ----------------------------------------------------------------
TTS_ENGINE = "edge-tts"  # "edge-tts" or "pyttsx3"
TTS_RATE = 180
TTS_VOLUME = 1.0
EDGE_TTS_VOICE = "en-GB-RyanNeural"
EDGE_TTS_RATE = "+0%"
EDGE_TTS_PITCH = "+0Hz"
STT_PAUSE_THRESHOLD = 0.8
STT_ENERGY_THRESHOLD = 300

# --- Phone control (disabled by default) -----------------------------------
ENABLE_PHONE_SERVER = os.getenv("RAGVA_ENABLE_PHONE_SERVER", "0") == "1"
PHONE_SERVER_HOST = os.getenv("RAGVA_PHONE_HOST", "127.0.0.1")
PHONE_SERVER_PORT = int(os.getenv("RAGVA_PHONE_PORT", "5005"))
