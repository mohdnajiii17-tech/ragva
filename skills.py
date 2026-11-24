"""
RAGVA Skills
=============
Real actions RAGVA can take on your Windows PC. Each skill is described as
an Anthropic "tool" so Claude can decide when to call it, plus the Python
function that actually does the work.

Add your own by: (1) adding an entry to TOOLS, (2) adding a branch in
execute_tool(), (3) writing the function.
"""
import os
import sys
import platform
import subprocess
import webbrowser
import re
import ctypes
from datetime import datetime, timezone, timedelta

import requests

NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.txt")

# Friendly name -> Windows launch command
APP_COMMANDS = {
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "file explorer": "explorer",
    "explorer": "explorer",
    "word": "winword",
    "microsoft word": "winword",
    "excel": "excel",
    "microsoft excel": "excel",
    "powerpoint": "powerpnt",
    "spotify": "spotify",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "windows terminal": "wt",
    "command prompt": "cmd",
    "cmd": "cmd",
    "task manager": "taskmgr",
    "paint": "mspaint",
    "settings": "start ms-settings:",
}

# ---------------------------------------------------------------------------
# Tool schemas (Anthropic tool-use format)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "open_app",
        "description": "Open/launch an application on the user's Windows PC, e.g. notepad, chrome, spotify, calculator, file explorer, task manager.",
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "Name of the app to open, e.g. 'notepad' or 'chrome'"}},
            "required": ["app_name"],
        },
    },
    {
        "name": "open_website",
        "description": "Open a website in the user's default browser.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL or domain to open, e.g. 'youtube.com'"}},
            "required": ["url"],
        },
    },
    {
        "name": "get_time",
        "description": "Get the current local date and time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for a named location (city/town).",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string", "description": "City or place name, e.g. 'Bidar, India'"}},
            "required": ["location"],
        },
    },
    {
        "name": "lock_pc",
        "description": "Lock the user's Windows PC immediately (like pressing Win+L).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "take_note",
        "description": "Save a short note/reminder for the user to a local notes file, timestamped.",
        "input_schema": {
            "type": "object",
            "properties": {"note": {"type": "string", "description": "The note text to save"}},
            "required": ["note"],
        },
    },
    {
        "name": "read_notes",
        "description": "Read back all previously saved notes.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_battery",
        "description": "Get the laptop's current battery percentage and charging status.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_command",
        "description": "Run any Windows command-line/PowerShell command on the user's PC and return its output. Use for things not covered by other skills: listing files, reading file contents, checking system info, running scripts, managing files/folders, etc. This is powerful - explain to the user what a command will do before running anything destructive (delete, format, etc).",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "The command to run, e.g. 'dir C:\\Users' or 'type notes.txt'"}},
            "required": ["command"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for current information, facts, or answers not already known.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to search for"}},
            "required": ["query"],
        },
    },
    {
        "name": "browse_webpage",
        "description": "Fetch and read the text content of a specific webpage URL.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "The URL to fetch, e.g. 'https://example.com'"}},
            "required": ["url"],
        },
    },
    {
        "name": "get_calendar_events",
        "description": "Get the user's upcoming calendar events/appointments from Outlook for the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {"days_ahead": {"type": "integer", "description": "How many days ahead to look, default 7"}},
        },
    },
    {
        "name": "add_calendar_event",
        "description": "Add a new appointment/event to the user's Outlook calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Title of the event"},
                "start_time": {"type": "string", "description": "Start date/time, e.g. '2026-09-20 15:00'"},
                "duration_minutes": {"type": "integer", "description": "How long the event lasts in minutes, default 60"},
            },
            "required": ["subject", "start_time"],
        },
    },
    {
        "name": "media_control",
        "description": "Control whatever media is currently playing (Spotify, YouTube, etc.) - play, pause, skip to next track, go to previous track, volume up, volume down, or mute.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["play_pause", "next", "previous", "volume_up", "volume_down", "mute"],
                    "description": "The media action to perform",
                }
            },
            "required": ["action"],
        },
    },
    {
        "name": "open_path",
        "description": "Open a specific file or folder by its full path on the user's PC (opens it in its default app / File Explorer).",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Full path to the file or folder, e.g. 'C:\\\\Users\\\\umair\\\\Documents'"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_folder",
        "description": "List the files and subfolders inside a given folder path.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Full folder path to list, e.g. 'C:\\\\Users\\\\umair\\\\Documents'"}},
            "required": ["path"],
        },
    },
    {
        "name": "search_files",
        "description": "Search for files by name (partial match) within a given folder, searching subfolders too.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "Folder to search within, e.g. 'C:\\\\Users\\\\umair\\\\Documents'"},
                "name_contains": {"type": "string", "description": "Text the filename should contain"},
            },
            "required": ["folder", "name_contains"],
        },
    },
]


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------
def open_app(app_name: str) -> str:
    key = app_name.lower().strip()
    cmd = APP_COMMANDS.get(key, app_name)
    try:
        if platform.system() == "Windows":
            os.system(f'start "" {cmd}')
        else:
            os.system(cmd)
        return f"Opened {app_name}."
    except Exception as e:
        return f"Couldn't open {app_name}: {e}"


def open_website(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url} in your browser."


def get_time() -> str:
    now = datetime.now()
    return now.strftime("It's %I:%M %p on %A, %B %d, %Y.")


def get_weather(location: str) -> str:
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1},
            timeout=8,
        ).json()
        if not geo.get("results"):
            return f"I couldn't find a place called '{location}'."
        place = geo["results"][0]
        lat, lon = place["latitude"], place["longitude"]
        name = f"{place.get('name')}, {place.get('country', '')}".strip(", ")

        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"},
            timeout=8,
        ).json()
        cur = wx.get("current", {})
        temp = cur.get("temperature_2m")
        humidity = cur.get("relative_humidity_2m")
        wind = cur.get("wind_speed_10m")
        return f"In {name}: {temp}°C, {humidity}% humidity, wind {wind} km/h."
    except Exception as e:
        return f"Couldn't fetch the weather: {e}"


def lock_pc() -> str:
    try:
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "PC locked."
        return "Locking is only supported on Windows."
    except Exception as e:
        return f"Couldn't lock the PC: {e}"


def take_note(note: str) -> str:
    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}\n")
        return "Noted."
    except Exception as e:
        return f"Couldn't save the note: {e}"


def read_notes() -> str:
    if not os.path.exists(NOTES_FILE):
        return "You don't have any notes yet."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return content if content else "You don't have any notes yet."


def get_battery() -> str:
    try:
        import psutil
        batt = psutil.sensors_battery()
        if batt is None:
            return "No battery detected (probably a desktop)."
        status = "charging" if batt.power_plugged else "on battery"
        return f"Battery is at {batt.percent}%, currently {status}."
    except Exception as e:
        return f"Couldn't read the battery: {e}"


def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = (result.stdout or "") + (result.stderr or "")
        output = output.strip()
        if not output:
            output = f"(command completed, exit code {result.returncode}, no output)"
        return output[:2000]
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"


def web_search(query: str) -> str:
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=5))
        if not results:
            return "No search results found."
        lines = []
        for r in results:
            lines.append(f"- {r.get('title', '')}: {r.get('body', '')} ({r.get('href', '')})")
        return "\n".join(lines)[:2000]
    except Exception as e:
        return f"Search error: {e}"


def browse_webpage(url: str) -> str:
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        text = re.sub(r"<script.*?</script>|<style.*?</style>", "", resp.text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:3000] if text else "Page loaded but no readable text found."
    except Exception as e:
        return f"Couldn't fetch that page: {e}"


# ---------------------------------------------------------------------------
# Outlook Calendar (uses your existing Outlook desktop app via COM - no
# extra login/setup needed if Outlook is already installed and signed in)
# ---------------------------------------------------------------------------
def get_calendar_events(days_ahead: int = 7) -> str:
    try:
        import win32com.client
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        calendar = outlook.GetDefaultFolder(9)  # 9 = olFolderCalendar
        items = calendar.Items
        items.IncludeRecurrences = True
        items.Sort("[Start]")

        now = datetime.now()
        end = now + timedelta(days=days_ahead or 7)
        restriction = f"[Start] >= '{now.strftime('%m/%d/%Y %H:%M')}' AND [Start] <= '{end.strftime('%m/%d/%Y %H:%M')}'"
        restricted = items.Restrict(restriction)

        events = []
        for item in restricted:
            events.append(f"- {item.Subject} at {item.Start.strftime('%a %b %d, %I:%M %p')}")
            if len(events) >= 15:
                break

        if not events:
            return f"No events found in the next {days_ahead or 7} days."
        return "\n".join(events)
    except Exception as e:
        return f"Couldn't read the calendar (is Outlook installed and set up?): {e}"


def add_calendar_event(subject: str, start_time: str, duration_minutes: int = 60) -> str:
    try:
        import win32com.client
        outlook = win32com.client.Dispatch("Outlook.Application")
        appt = outlook.CreateItem(1)  # 1 = olAppointmentItem
        appt.Subject = subject
        appt.Start = start_time
        appt.Duration = duration_minutes or 60
        appt.Save()
        return f"Added '{subject}' to your calendar at {start_time}."
    except Exception as e:
        return f"Couldn't add that event (is Outlook installed and set up?): {e}"


# ---------------------------------------------------------------------------
# Media control (works with Spotify, YouTube, or anything else playing -
# simulates the same media keys a real keyboard has, no login required)
# ---------------------------------------------------------------------------
_VK_MEDIA = {
    "play_pause": 0xB3,
    "next": 0xB0,
    "previous": 0xB1,
    "volume_up": 0xAF,
    "volume_down": 0xAE,
    "mute": 0xAD,
}


def media_control(action: str) -> str:
    vk = _VK_MEDIA.get(action)
    if not vk:
        return f"Unknown media action: {action}"
    try:
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)  # KEYEVENTF_KEYUP
        return f"Done: {action.replace('_', ' ')}."
    except Exception as e:
        return f"Couldn't control media: {e}"


# ---------------------------------------------------------------------------
# File / folder access
# ---------------------------------------------------------------------------
def open_path(path: str) -> str:
    try:
        os.startfile(path)
        return f"Opened {path}."
    except Exception as e:
        return f"Couldn't open {path}: {e}"


def list_folder(path: str) -> str:
    try:
        entries = os.listdir(path)
        if not entries:
            return f"{path} is empty."
        lines = []
        for e in entries[:50]:
            full = os.path.join(path, e)
            marker = "[folder]" if os.path.isdir(full) else "[file]"
            lines.append(f"{marker} {e}")
        return "\n".join(lines)
    except Exception as e:
        return f"Couldn't list {path}: {e}"


def search_files(folder: str, name_contains: str) -> str:
    try:
        matches = []
        needle = name_contains.lower()
        for root, dirs, files in os.walk(folder):
            for f in files:
                if needle in f.lower():
                    matches.append(os.path.join(root, f))
                    if len(matches) >= 20:
                        return "\n".join(matches)
        if not matches:
            return f"No files matching '{name_contains}' found in {folder}."
        return "\n".join(matches)
    except Exception as e:
        return f"Couldn't search {folder}: {e}"


_DISPATCH = {
    "open_app": lambda i: open_app(i["app_name"]),
    "open_website": lambda i: open_website(i["url"]),
    "get_time": lambda i: get_time(),
    "get_weather": lambda i: get_weather(i["location"]),
    "lock_pc": lambda i: lock_pc(),
    "take_note": lambda i: take_note(i["note"]),
    "read_notes": lambda i: read_notes(),
    "get_battery": lambda i: get_battery(),
    "run_command": lambda i: run_command(i["command"]),
    "web_search": lambda i: web_search(i["query"]),
    "browse_webpage": lambda i: browse_webpage(i["url"]),
    "get_calendar_events": lambda i: get_calendar_events(i.get("days_ahead", 7)),
    "add_calendar_event": lambda i: add_calendar_event(i["subject"], i["start_time"], i.get("duration_minutes", 60)),
    "media_control": lambda i: media_control(i["action"]),
    "open_path": lambda i: open_path(i["path"]),
    "list_folder": lambda i: list_folder(i["path"]),
    "search_files": lambda i: search_files(i["folder"], i["name_contains"]),
}


def execute_tool(name: str, tool_input: dict) -> str:
    fn = _DISPATCH.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return fn(tool_input)
    except Exception as e:
        return f"Error running {name}: {e}"
