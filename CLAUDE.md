# CLAUDE.md

Guidance for Claude when working in this repository.

## Project overview

A single-file Python desktop app: a Rocket League "quick chat" macro tool.
It listens for global `V` / `R` / `F` keypresses and, when scanning is
enabled (`F6`)/disabled (`F7`), opens team or all chat, types a
user-configured phrase, and presses Enter — via `pynput`.

Main file: `Custom_Quick_Chat_V3.py` (Tkinter GUI + pynput keyboard hook).

## Tech stack

- Python 3.9+
- Tkinter for the GUI (dark theme, canvas-drawn rounded rectangles/buttons)
- `pynput` for global keyboard listening and synthetic keystrokes
- `json` for persisted settings (`quickchat_config.json`)
- No build system / package manager — it's a single script, run directly

## Architecture notes

- **Global mutable state** (`scanning_enabled`, `is_typing`, `gui_focused`,
  `suppress_keys`, `phrases`, `chat_keys`, `listener`, `last_trigger_time`)
  lives at module scope and is shared between the Tkinter main thread, the
  `pynput` listener thread, and short-lived worker threads spawned per
  trigger (`send_phrase`). Keep this in mind before adding new state —
  prefer plain dicts/threading-safe primitives over anything requiring
  locks unless a real race condition shows up.
- **`try_trigger`** is the gatekeeper for firing a phrase: checks
  `scanning_enabled`, `is_typing`, `gui_focused`, and the cooldown before
  spawning a worker thread. Any new trigger source should go through this
  function rather than calling `send_phrase` directly.
- **Windows-only suppression** happens via `win32_event_filter` passed to
  `pynput.keyboard.Listener`. On non-Windows platforms this is inert; the
  checkbox is disabled and `suppress_keys` is forced `False` at startup.
  Don't assume `win32_event_filter` runs cross-platform.
- **Self-trigger guard**: synthetic keystrokes from `send_phrase` are marked
  with `LLKHF_INJECTED` and skipped in `win32_event_filter`. Any new
  synthetic-input code path must preserve this guard or the tool will fire
  on its own output.
- **Persistence**: `load_config()` / `save_config()` read/write
  `quickchat_config.json` next to the script (or next to the frozen `.exe`
  via `sys.frozen`/`sys.executable`). Config is saved on **Start Listening**
  and on **Stop & Exit**/window close. When adding new configurable fields,
  extend both functions together and keep the JSON schema backward
  compatible (default-fill missing keys rather than raising).

## Working conventions (from prior sessions)

- **Iterative, targeted changes.** The user evaluates results quickly and
  asks for specific tweaks rather than full rewrites. Prefer small,
  surgical diffs over restructuring working code.
- **Preserve working backend logic when making visual/GUI changes**, and
  vice versa — don't let a styling request touch trigger/listener logic,
  and don't let a logic fix quietly change the GUI layout.
- **Windows is the primary target platform** (this is a Rocket League tool);
  cross-platform behavior is a secondary concern but shouldn't be broken
  outright — degrade gracefully like the existing `suppress_keys` checkbox
  does.
- Match the existing dark theme constants (`BG_MAIN`, `BG_PANEL`,
  `ACCENT_GREEN`, `ACCENT_RED`, etc.) and the canvas-based rounded-rectangle
  pattern (`round_rectangle`, `make_rounded_button`) instead of introducing
  a new styling approach.

## Running / testing

```bash
pip install pynput
python Custom_Quick_Chat_V3.py
```

There is no automated test suite. Tkinter + global keyboard hooks are hard
to unit test meaningfully; verify changes by running the GUI manually and
checking the in-app activity log. When possible, run
`python -m py_compile Custom_Quick_Chat_V3.py` as a quick syntax sanity
check before handing back changes.

## Repo layout

```
.
├── Custom_Quick_Chat_V3.py   # main application (GUI + macro logic)
├── quickchat_config.json     # generated at runtime, not committed
├── README.md
├── LICENSE                   # MIT
└── CLAUDE.md                 # this file
```
