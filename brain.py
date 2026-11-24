"""
The "brain" of RAGVA: sends the conversation to Groq (fast cloud AI),
lets it call skills/tools when needed, and returns the final reply.
"""
import json
import threading

from groq import Groq

import config
from skills import TOOLS, execute_tool

_client = Groq(api_key=config.GROQ_API_KEY)
_history = []  # list of {"role": ..., "content": ..., ...}
_lock = threading.Lock()  # guards _history since voice/typed/phone commands can now arrive concurrently
MAX_TOOL_ITERATIONS = 5


def _to_groq_tools():
    """Convert our tool schemas into the OpenAI-style format Groq expects."""
    converted = []
    for t in TOOLS:
        converted.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        })
    return converted


_GROQ_TOOLS = _to_groq_tools()


def ask(user_text: str) -> str:
    global _history
    with _lock:
        _history.append({"role": "user", "content": user_text})

        reply = ""
        for _ in range(MAX_TOOL_ITERATIONS):
            response = _client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "system", "content": config.SYSTEM_PROMPT}] + _history,
                tools=_GROQ_TOOLS,
                max_tokens=800,
            )
            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            assistant_entry = {"role": "assistant", "content": msg.content or ""}
            if tool_calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ]
            _history.append(assistant_entry)

            if not tool_calls:
                reply = (msg.content or "").strip()
                break

            for tc in tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                result = execute_tool(name, args)
                _history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })
        else:
            reply = "Sorry, I got stuck trying to use my tools too many times."

        if not reply:
            reply = "Done."

        _trim_history()
        return reply


def _trim_history():
    global _history
    max_items = config.MAX_HISTORY_TURNS * 4
    if len(_history) > max_items:
        _history = _history[-max_items:]


def reset_history():
    global _history
    _history = []