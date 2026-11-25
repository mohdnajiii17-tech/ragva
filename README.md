# RAGVA

**VOICE-FIRST · WINDOWS DESKTOP ASSISTANT**

A JARVIS-style HUD with a cloud LLM brain and real OS actions — type, talk, or command it from your phone.

*17 skills · Groq tool-calling · Python 3.10+ · pywebview HUD · edge-tts voice*

> This README is transcribed from the three concept sheets in [`assets/`](assets/) (`banner.pdf`, `thumbnail.pdf`, `preview-grid.pdf`). The interface preview below is a **stylized mockup, not a live screenshot**. For setup, architecture, limitations and security notes, see the [full project documentation](<README(RAGVA) (2)>).

---

## Interface preview

`hud.html` · full mode · **4 states**

| State | Label | Meaning |
|---|---|---|
| Idle | `IDLE // STANDBY` | Waiting for input |
| Listening | `LISTENING // AUDIO ACTIVE` | Microphone capture |
| Processing | `PROCESSING // NEURAL SYNTHESIS` | Model/tool processing |
| Synthesizing | `SYNTHESIZING // CELESTIAL REPLY` | Spoken response |

Input: **“type a command… ENGAGE”**

### Example command flow

```text
YOU          lock my pc
RAGVA.PY     process_query() → status: Thinking…
BRAIN.PY     Groq chat.completions + tools
TOOL_CALL    lock_pc → LockWorkStation()
TOOL RESULT  string returned to the model
RAGVA        reply → HUD log + edge-tts voice
```

**max 5 tool hops per turn · one request at a time**

## Skills

`skills.py` · **17 tools** · schema in `TOOLS` · callable in `_DISPATCH`

| Category | Tools |
|---|---|
| Apps & web | `open_app`, `open_website`, `browse_webpage`, `web_search` |
| System | `lock_pc`, `run_command`, `get_battery`, `media_control` |
| Info | `get_time`, `get_weather` |
| Files | `open_path`, `list_folder`, `search_files` |
| Notes & calendar | `take_note`, `read_notes`, `get_calendar_events`, `add_calendar_event` |

## Concept sheets

- [Banner](assets/banner.pdf)
- [Thumbnail](assets/thumbnail.pdf)
- [Preview grid](assets/preview-grid.pdf)

## Before running

Review the [security section](<README(RAGVA) (2)>) of the full documentation first: the prototype has documented risks around embedded credentials, shell command execution, an unauthenticated LAN endpoint, and cloud data disclosure.
