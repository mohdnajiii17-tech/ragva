# RAGVA — Preview grid

![RAGVA interface preview grid](assets/previews/preview-grid.png)

> Interface preview · stylized mockup, not a live screenshot.

`hud.html` · full mode · **4 states**

| State | Label | Meaning |
|---|---|---|
| Idle | `IDLE // STANDBY` | Waiting for input |
| Listening | `LISTENING // AUDIO ACTIVE` | Microphone capture |
| Processing | `PROCESSING // NEURAL SYNTHESIS` | Model/tool processing |
| Synthesizing | `SYNTHESIZING // CELESTIAL REPLY` | Spoken response |

Input: **“type a command… ENGAGE”**

## Example command flow

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

[Download the source PDF](assets/preview-grid.pdf) · [Main README](README.md)
