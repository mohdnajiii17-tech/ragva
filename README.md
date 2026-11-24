# RAGVA — Your Personal AI Assistant (Windows)

A JARVIS-style assistant that runs on your laptop, talks to you through your
speakers, listens through your mic, and thinks using Claude.

## What it does
- **A small on-screen HUD** (always-on-top panel) with a conversation log,
  a text box, and a mic button.
- **Speaks every reply out loud** through your default Windows speaker/output.
- **Listens in the background** for the wake word `"ragva"` — say
  *"RAGVA, what's the weather like"* and it'll respond.
- **Also works as typed chat** — type in the HUD and press Enter.
- **Push-to-talk**: tap the 🎤 button to speak one command any time.
- **Can actually DO things** (not just talk) — see "Skills" below.
- Remembers the last ~20 turns of conversation so it has context.

## Skills — what it can actually do
RAGVA can call these on your PC when it decides they're useful (you can just
ask naturally — e.g. "open Spotify", "what's the weather in Bidar",
"lock my PC", "note that I need to renew my license"):

| Skill | Example |
|---|---|
| Open an app | "open notepad" / "launch chrome" |
| Open a website | "open youtube.com" |
| Check the time | "what time is it" |
| Check the weather | "what's the weather in Bidar" |
| Lock the PC | "lock my computer" |
| Save a note | "note that I need to call mom" |
| Read notes back | "what are my notes" |
| Check battery | "how much battery do I have" |

Add more yourself in `skills.py` — each one is just a Python function plus a
short description; Claude figures out when to call it.

## 1. Install Python
If you don't already have it: download Python 3.10+ from
https://www.python.org/downloads/windows/ and during install, check
**"Add python.exe to PATH"**.

## 2. Get the files
Unzip this folder anywhere, e.g. `C:\RAGVA\`.

## 3. Install dependencies
Open **Command Prompt** in the `RAGVA` folder (Shift+Right-click inside the
folder → "Open PowerShell/Terminal window here") and run:

```
pip install -r requirements.txt
```

**Note on PyAudio (needed for the microphone):** if `pip install pyaudio`
fails on Windows, run this instead:

```
pip install pipwin
pipwin install pyaudio
```

## 4. Add your Anthropic API key
1. Get a key from https://console.anthropic.com/settings/keys
2. Open `config.py` in Notepad
3. Replace `sk-ant-your-key-here` with your real key
4. Save

## 5. Set your speaker/mic as default (Windows)
Right-click the speaker icon in your taskbar → **Sound settings** → make sure
your desired **Output** (speaker) and **Input** (microphone) devices are set
as default. RAGVA uses whatever Windows considers the default device.

## 6. Run it
```
python ragva.py
```

A small HUD window will pop up and you should hear "RAGVA online. How can I
help?" Then either:
- Say **"RAGVA, ..."** followed by your request, or
- Type your message in the box and press Enter, or
- Tap the 🎤 button and speak one command (push-to-talk)

Say/type `exit` to quit, or `reset` to clear its memory of the conversation.

## Customizing
Everything is in `config.py`:
- `WAKE_WORD` — change from "ragva" to anything else
- `MODEL` — which Claude model it uses
- `SYSTEM_PROMPT` — its personality/instructions
- `TTS_ENGINE` — `"pyttsx3"` (offline, robotic-ish, built into Windows) or
  `"edge-tts"` (needs internet, much more natural-sounding voices — try
  changing `EDGE_TTS_VOICE` too, e.g. `"en-GB-RyanNeural"`)
- `CONTINUOUS_LISTEN` — set to `False` if you only want push-to-talk / typed
  input (no background wake-word listening)

## Running it on startup / making it "always on"
Create a shortcut to `ragva.py`, or a `.bat` file like:
```
@echo off
cd /d C:\RAGVA
python ragva.py
pause
```
and drop that `.bat` shortcut in your Startup folder
(`Win+R` → `shell:startup`) if you want it to launch automatically.

## Where this can go next
- More skills: calendar/email integration, Spotify control, smart-home
  control, opening specific files/folders, running scripts
- A custom wake-word engine (e.g. Porcupine) instead of Google's speech API,
  for faster/more private wake-word detection
- Streaming responses so it starts speaking before the full reply is done
- A fancier HUD (waveform animation, transparency, system tray icon)

Happy to help build any of these next.
