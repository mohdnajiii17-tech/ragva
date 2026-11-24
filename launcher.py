"""
RAGVA Launcher
===============
A lightweight, always-on background listener. It does NOT load the AI model
or the HUD - it just quietly listens for your launch phrase and starts the
full RAGVA app when it hears it.

Run this at Windows startup (see README.md) so RAGVA can launch itself
anytime, even if you haven't opened anything yet.
"""
import os
import sys
import subprocess
import time

import sounddevice as sd
import speech_recognition as sr

import config

_recognizer = sr.Recognizer()
_SAMPLE_RATE = 16000
_CHUNK_SECONDS = 4  # how long each listening chunk records for

LAUNCH_PHRASE = getattr(config, "LAUNCH_PHRASE", "ragva wake up").lower()
RAGVA_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ragva.py")


def _listen_chunk(duration=_CHUNK_SECONDS) -> str:
    try:
        recording = sd.rec(int(duration * _SAMPLE_RATE), samplerate=_SAMPLE_RATE, channels=1, dtype="int16")
        sd.wait()
    except Exception as e:
        print(f"[microphone error: {e}]")
        time.sleep(2)
        return ""

    audio_data = sr.AudioData(recording.tobytes(), _SAMPLE_RATE, 2)
    try:
        return _recognizer.recognize_google(audio_data).lower()
    except (sr.UnknownValueError, sr.RequestError):
        return ""


def main():
    print(f'RAGVA launcher is running quietly in the background.')
    print(f'Say "{LAUNCH_PHRASE}" anytime to start RAGVA.')
    while True:
        heard = _listen_chunk()
        if heard:
            print(f"[heard] {heard}")
        if LAUNCH_PHRASE in heard:
            print("Launch phrase detected - starting RAGVA...")
            # Run the full app and wait for it to close before listening again,
            # so the launcher and the full app never fight over the microphone.
            subprocess.run([sys.executable, RAGVA_SCRIPT])
            print("RAGVA closed. Listening for the launch phrase again...")


if __name__ == "__main__":
    main()
