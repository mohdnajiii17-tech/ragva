"""
RAGVA Phone Server
===================
A tiny local web server so your phone (e.g. an iPhone Siri Shortcut) can send
text commands to RAGVA over your home WiFi - no cloud, no accounts, just your
PC and phone on the same network.

Endpoint:
  POST /command   body: {"text": "what time is it"}   -> {"reply": "..."}
  GET  /ping       -> "ok"  (use this to test connectivity first)
"""
import threading

from flask import Flask, request, jsonify

import config
import brain
from audio_io import speak

app = Flask(__name__)


@app.route("/ping", methods=["GET"])
def ping():
    return "ok"


@app.route("/command", methods=["POST"])
def command():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "no 'text' provided"}), 400

    print(f"\033[95m[phone]\033[0m {text}")
    try:
        reply = brain.ask(text)
    except Exception as e:
        reply = "I hit an error talking to my brain."
        print(f"[phone command error] {e}")

    # Also speak it out loud on the PC, same as any other command
    threading.Thread(target=speak, args=(reply,), daemon=True).start()
    return jsonify({"reply": reply})


def run_server(host="0.0.0.0", port=5005):
    print(f"\033[93m[phone server running on port {port} - find your PC's IP with 'ipconfig']\033[0m")
    app.run(host=host, port=port, debug=False, use_reloader=False)


def start_in_background(port=5005):
    t = threading.Thread(target=run_server, kwargs={"port": port}, daemon=True)
    t.start()
    return t