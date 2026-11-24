"""
RAGVA HUD (web-based)
======================
Hosts hud.html as a real native desktop window using pywebview, with a
Python<->JS bridge so every element in the HUD is wired to real backend
behavior (real listening, real Groq replies, real logs) instead of the
original mockup's simulated states.
"""
import json
import os
import threading

import webview

_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hud.html")

# Maps our internal status keys to the HUD's JS state names
_STATE_MAP = {
    "idle": "idle",
    "listening": "listening",
    "thinking": "thinking",
    "speaking": "speaking",
    "offline": "idle",
}


class _JsApi:
    """Methods callable from the HTML/JS side via window.pywebview.api.*"""

    def __init__(self, on_submit, on_mic):
        self._on_submit = on_submit
        self._on_mic = on_mic or (lambda: None)

    def submit(self, text):
        threading.Thread(target=self._on_submit, args=(text,), daemon=True).start()
        return None

    def mic_click(self):
        threading.Thread(target=self._on_mic, daemon=True).start()
        return None


class RagvaGUI:
    """Same interface as the old Tkinter RagvaGUI (post_status, post_message,
    shutdown, run) so ragva.py doesn't need to change how it talks to the GUI."""

    def __init__(self, on_submit, on_mic=None, assistant_name="RAGVA"):
        self.assistant_name = assistant_name
        self._api = _JsApi(on_submit, on_mic)
        self.window = webview.create_window(
            assistant_name,
            _HTML_PATH,
            js_api=self._api,
            width=480,
            height=760,
            min_size=(360, 480),
            background_color="#020306",
        )

    def post_status(self, text: str, key: str):
        js_state = _STATE_MAP.get(key, "idle")
        self._eval(f"setAgentState('{js_state}')")

    def post_message(self, who: str, text: str):
        label = "YOU" if who != self.assistant_name else self.assistant_name.upper()
        self._eval(f"addLog({json.dumps(label)}, {json.dumps(text)})")

    def shutdown(self, delay_ms=400):
        threading.Timer(delay_ms / 1000, self._destroy).start()

    def run(self):
        webview.start()

    # -- internal -----------------------------------------------------------
    def _eval(self, js: str):
        try:
            self.window.evaluate_js(js)
        except Exception as e:
            print(f"[hud js error] {e}")

    def _destroy(self):
        try:
            self.window.destroy()
        except Exception:
            pass
