"""
Audio input/output for RAGVA: microphone listening (STT) and
speaking replies out loud through your speakers (TTS).
"""
import threading
import tempfile
import os
import time

import numpy as np
import sounddevice as sd
import speech_recognition as sr

import config

_speak_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Text-to-speech
# ---------------------------------------------------------------------------
def _speak_pyttsx3(text: str):
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", config.TTS_RATE)
    engine.setProperty("volume", config.TTS_VOLUME)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def speak(text: str):
    """Speak `text` out loud through the default Windows speaker/output device."""
    if not text:
        return
    with _speak_lock:
        print(f"\033[96m{config.ASSISTANT_NAME}:\033[0m {text}")
        try:
            if config.TTS_ENGINE == "edge-tts":
                _speak_edge_tts(text)
            else:
                _speak_pyttsx3(text)
        except Exception as e:
            print(f"[speech error: {e}]")


def _speak_edge_tts(text: str):
    import asyncio
    import edge_tts
    from playsound import playsound

    async def _gen(path):
        communicate = edge_tts.Communicate(
            text,
            config.EDGE_TTS_VOICE,
            rate=getattr(config, "EDGE_TTS_RATE", "+0%"),
            pitch=getattr(config, "EDGE_TTS_PITCH", "+0Hz"),
        )
        await communicate.save(path)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        path = f.name
    try:
        asyncio.run(_gen(path))
        playsound(path)
    finally:
        os.remove(path)


# ---------------------------------------------------------------------------
# Speech-to-text
# ---------------------------------------------------------------------------
# Uses sounddevice to record (no compiler needed) and Google's free web
# speech API to transcribe (no local native DLLs - avoids Application
# Control policy restrictions some managed PCs have against onnxruntime/etc).
_recognizer = sr.Recognizer()
_SAMPLE_RATE = 16000
_BLOCK_SIZE = 1024


def listen_once(timeout=None, phrase_time_limit=8) -> str:
    """Record from the default mic until you go quiet (or `phrase_time_limit`
    seconds pass, whichever comes first), then return the transcribed text
    (empty string if nothing understood)."""
    max_duration = phrase_time_limit or 8
    silence_limit = getattr(config, "STT_PAUSE_THRESHOLD", 0.8)
    threshold = getattr(config, "STT_ENERGY_THRESHOLD", 300)
    min_speech_seconds = 0.25

    frames = []
    state = {"speech_started": False, "silence_since": None, "speech_seconds": 0.0}

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())
        volume = float(np.abs(indata).mean())
        block_seconds = frame_count / _SAMPLE_RATE
        if volume > threshold:
            state["speech_started"] = True
            state["silence_since"] = None
            state["speech_seconds"] += block_seconds
        elif state["speech_started"] and state["silence_since"] is None:
            state["silence_since"] = time.time()

    print(f"\033[93m[listening...]\033[0m")
    try:
        with sd.InputStream(samplerate=_SAMPLE_RATE, channels=1, dtype="int16",
                             blocksize=_BLOCK_SIZE, callback=callback):
            start = time.time()
            while True:
                elapsed = time.time() - start
                if elapsed > max_duration:
                    break
                if (state["speech_started"] and state["speech_seconds"] >= min_speech_seconds
                        and state["silence_since"] is not None
                        and (time.time() - state["silence_since"]) > silence_limit):
                    break
                sd.sleep(40)
    except Exception as e:
        print(f"[microphone error: {e}]")
        return ""

    if not frames or not state["speech_started"]:
        return ""

    recording = np.concatenate(frames, axis=0)
    audio_data = sr.AudioData(recording.tobytes(), _SAMPLE_RATE, 2)
    try:
        text = _recognizer.recognize_google(audio_data)
        print(f"\033[92mYou (voice):\033[0m {text}")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"[speech recognition service error: {e}]")
        return ""


def listen_for_wake_word_loop(on_command, stop_event: threading.Event):
    """Background loop that continuously listens.

    If config.REQUIRE_WAKE_WORD is False (default), anything understood is
    passed straight to on_command() - no wake word needed once running.

    If True, it waits to hear the wake word before treating speech as a
    command (the old behavior).
    """
    require_wake = getattr(config, "REQUIRE_WAKE_WORD", False)
    wake = config.WAKE_WORD.lower()

    while not stop_event.is_set():
        heard = listen_once(timeout=5, phrase_time_limit=6)
        if not heard:
            continue

        if not require_wake:
            on_command(heard)
            continue

        lower = heard.lower()
        if wake in lower:
            remainder = lower.split(wake, 1)[1].strip()
            if remainder:
                on_command(remainder)
            else:
                speak("Yes?")
                follow_up = listen_once(timeout=6, phrase_time_limit=10)
                if follow_up:
                    on_command(follow_up)