"""
JARVIS - Personal AI Assistant
==============================
Run this file to start RAGVA. It will:
  - Open a small on-screen HUD you can type into
  - Speak every reply out loud through your speakers
  - Listen in the background for your wake word ("ragva") + a spoken command
  - Let you press the mic button for push-to-talk
  - Actually DO things: open apps/websites, check weather/time/battery,
    lock your PC, take notes (see skills.py for the full list)

Setup: see README.md
"""
import threading

import config
import brain
from audio_io import speak, listen_once, listen_for_wake_word_loop
from gui_web import RagvaGUI
import phone_server

stop_event = threading.Event()
gui: RagvaGUI = None


def set_status(text, key):
    gui.post_status(text, key)


def process_query(text: str):
    text = text.strip()
    if not text:
        return
    low = text.lower()
    gui.post_message("You", text)

    if low in ("exit", "quit", "shut down ragva", "goodbye"):
        set_status("Offline", "offline")
        speak("Goodbye.")
        stop_event.set()
        gui.shutdown()
        return

    if low in ("reset", "clear memory", "forget everything"):
        brain.reset_history()
        reply = "Memory cleared."
        gui.post_message(config.ASSISTANT_NAME, reply)
        set_status("Idle", "idle")
        speak(reply)
        return

    set_status("Thinking...", "thinking")
    try:
        reply = brain.ask(text)
    except Exception as e:
        reply = "I hit an error talking to my brain. Check the console for details."
        print(f"[error] {e}")

    gui.post_message(config.ASSISTANT_NAME, reply)
    set_status("Speaking...", "speaking")
    speak(reply)
    set_status(
        "Listening..." if config.CONTINUOUS_LISTEN else "Idle",
        "listening" if config.CONTINUOUS_LISTEN else "idle",
    )


def on_text_submit(text: str):
    threading.Thread(target=process_query, args=(text,), daemon=True).start()


def on_mic_click():
    def _run():
        set_status("Listening...", "listening")
        heard = listen_once(timeout=8, phrase_time_limit=15)
        if heard:
            process_query(heard)
        else:
            set_status("Idle", "idle")
    threading.Thread(target=_run, daemon=True).start()


def voice_wake_handler(text: str):
    process_query(text)


def voice_thread_target():
    if config.CONTINUOUS_LISTEN:
        listen_for_wake_word_loop(on_command=voice_wake_handler, stop_event=stop_event)


def main():
    global gui
    gui = RagvaGUI(on_submit=on_text_submit, on_mic=on_mic_click, assistant_name=config.ASSISTANT_NAME)
    gui.post_message(
        config.ASSISTANT_NAME,
        f'Online. Say "{config.WAKE_WORD}", type below, or tap the mic.',
    )
    set_status(
        "Listening..." if config.CONTINUOUS_LISTEN else "Idle",
        "listening" if config.CONTINUOUS_LISTEN else "idle",
    )

    threading.Thread(
        target=lambda: speak(f"{config.ASSISTANT_NAME} online. How can I help?"),
        daemon=True,
    ).start()

    threading.Thread(target=voice_thread_target, daemon=True).start()

    if getattr(config, "ENABLE_PHONE_SERVER", True):
        phone_server.start_in_background(port=getattr(config, "PHONE_SERVER_PORT", 5005))

    gui.run()


if __name__ == "__main__":
    main()
