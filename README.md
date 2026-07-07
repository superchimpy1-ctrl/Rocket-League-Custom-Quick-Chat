![Version 2 Available](https://github.com/superchimpy1-ctrl/Rocket-League-Custom-Quick-Chat/releases/tag/version-2)

# Rocket League Quick Chat Tool 🎮

A simple desktop app that lets you bind three custom, fully-typed chat phrases to keyboard shortcuts in Rocket League — no more digging through the default Quick Chat wheel mid-match.

## How It Works

1. Enter up to three custom phrases in the GUI (for the `V`, `R`, and `F` keys).
2. Click **Start Listening**.
3. Press **F6** to enable scanning, **F7** to disable it.
4. While scanning is enabled, pressing `V`, `R`, or `F` in-game will:
   - Simulate pressing `T` to open the Rocket League chat box
   - Type out your custom phrase
   - Press `Enter` to send it

A short cooldown (0.5s) prevents accidental double-triggers, and a live status log in the GUI shows what the tool is doing.

## Features

- 🖥️ Simple Tkinter GUI — no config files to edit
- ⌨️ Global hotkeys via `pynput` (works while Rocket League is focused)
- 🟢/🔴 Visual status indicator for whether scanning is on or off
- 📜 Built-in activity log with timestamps
- 🛑 Clean start/stop controls, including safely stopping the keyboard listener

## Requirements

- Python 3.8+
- [`pynput`](https://pypi.org/project/pynput/)

Install dependencies:

```bash
pip install pynput
```

`tkinter` ships with most standard Python installations. On Linux, you may need to install it separately:

```bash
sudo apt-get install python3-tk
```

## Usage

```bash
python "Custom Chat V2.py"
```

1. Fill in your three phrases in the text boxes (leading spaces are fine if you want a space before the phrase).
2. Click **Start Listening**.
3. In Rocket League, press **F6** to enable scanning.
4. Press `V`, `R`, or `F` during a match to send your phrase.
5. Press **F7** at any time to disable scanning without closing the app.
6. Click **Stop & Exit** to shut everything down cleanly.

## ⚠️ Notes & Disclaimer

- This tool simulates keystrokes globally, so scanning should be **disabled (F7)** whenever you're typing normally (e.g., in chat, Discord, or a text field) to avoid accidental triggers.
- Use of input-automation tools may be against the terms of service of some games or platforms. Check Rocket League / Epic's current rules before using this in ranked or competitive play, and use at your own risk.
- Only tested for personal/casual use — not affiliated with or endorsed by Psyonix or Epic Games.

## License

MIT — feel free to fork, modify, and share.
