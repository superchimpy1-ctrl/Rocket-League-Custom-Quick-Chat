import sys
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from pynput.keyboard import Key, Controller, Listener
import os
import json

# ---- Global state ----
keyboard = Controller()
scanning_enabled = False
listener = None
last_trigger_time = 0.0
is_typing = False       # True while we synthesize keystrokes (prevents self-triggering)
gui_focused = True      # True while this window has focus (prevents triggers while editing)
suppress_keys = True    # Swallow v/r/f so they don't reach the game (Windows only)

WINDOWS = sys.platform == "win32"

TRIGGER_COOLDOWN = 0.5   # Seconds between triggers
CHAT_OPEN_DELAY = 0.08   # Wait for RL chat box to open before typing
SUBMIT_DELAY = 0.05      # Wait before pressing Enter

TRIGGER_KEYS = ("v", "r", "f")
phrases = {"v": "", "r": "", "f": ""}
chat_keys = {"v": "t", "r": "t", "f": "t"}  # 't' = team chat, 'y' = all chat

# ---- Persistence ----
# Save alongside the script (or the frozen exe) so phrases survive restarts.
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "quickchat_config.json")


def load_config():
    """Load saved phrases/chat-keys from disk. Returns a dict with defaults on failure."""
    defaults = {
        "phrases": {"v": "", "r": "", "f": ""},
        "chat_keys": {"v": "Team", "r": "Team", "f": "Team"},
    }
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("v", "r", "f"):
            if k in data.get("phrases", {}):
                defaults["phrases"][k] = data["phrases"][k]
            if k in data.get("chat_keys", {}):
                defaults["chat_keys"][k] = data["chat_keys"][k]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return defaults


def save_config():
    """Persist current phrases/chat-keys to disk."""
    data = {
        "phrases": dict(phrases),
        "chat_keys": {
            k: ("Team" if v == "t" else "All") for k, v in chat_keys.items()
        },
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


saved_config = load_config()

# win32 low-level hook constants
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
LLKHF_INJECTED = 0x10
VK_MAP = {ord("V"): "v", ord("R"): "r", ord("F"): "f"}

# ---- Dark theme palette ----
BG_MAIN = "#121212"
BG_PANEL = "#1c1c1c"
BG_ENTRY = "#242424"
BG_LOG = "#0e0e0e"
FG_TEXT = "#e6e6e6"
FG_SUBTEXT = "#9a9a9a"
ACCENT_GREEN = "#3ddc84"
ACCENT_RED = "#ff5c5c"
BORDER_COLOR = "#2e2e2e"
FONT_MAIN = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 17, "bold")
FONT_SUB = ("Segoe UI", 9)
FONT_LABEL = ("Segoe UI", 10, "bold")

if os.name == 'nt':
    os.system('')

RESET = '\033[0m'
BOLD = '\033[1m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'

def print_colored_text(text, color='', background='', style=''):
    formatted_text = f"{style}{color}{background}{text}{RESET}"
    print(formatted_text, end='', flush=True)

def Clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def main():
    logo = """
                    \033[38;5;196m /$$$$$$  /$$$$$$  /$$   /$$  /$$$$$$         /$$$$$$  /$$   /$$ /$$$$$$  /$$$$$$  /$$   /$$        /$$$$$$  /$$   /$$  /$$$$$$  /$$$$$$$$\033[0m
                    \033[38;5;202m|_  $$_/ /$$__  $$| $$$ | $$ /$$__  $$       /$$__  $$| $$  | $$|_  $$_/ /$$__  $$| $$  /$$/       /$$__  $$| $$  | $$ /$$__  $$|__  $$__/\033[0m
                    \033[38;5;202m  | $$  | $$  \ $$| $$$$| $$| $$  \__/      | $$  \ $$| $$  | $$  | $$  | $$  \__/| $$ /$$/       | $$  \__/| $$  | $$| $$  \ $$   | $$   \033[0m
                    \033[38;5;208m  | $$  | $$$$$$$$| $$ $$ $$|  $$$$$$       | $$  | $$| $$  | $$  | $$  | $$      | $$$$$/        | $$      | $$$$$$$$| $$$$$$$$   | $$   \033[0m
                    \033[38;5;208m  | $$  | $$__  $$| $$  $$$$ \____  $$      | $$  | $$| $$  | $$  | $$  | $$      | $$  $$        | $$      | $$__  $$| $$__  $$   | $$   \033[0m
                    \033[38;5;214m  | $$  | $$  | $$| $$\  $$$ /$$  \ $$      | $$/$$ $$| $$  | $$  | $$  | $$    $$| $$\  $$       | $$    $$| $$  | $$| $$  | $$   | $$   \033[0m
                    \033[38;5;214m /$$$$$$| $$  | $$| $$ \  $$|  $$$$$$/      |  $$$$$$/|  $$$$$$/ /$$$$$$|  $$$$$$/| $$ \  $$      |  $$$$$$/| $$  | $$| $$  | $$   | $$   \033[0m
                    \033[38;5;220m|______/|__/  |__/|__/  \__/ \______/        \____ $$$ \______/ |______/ \______/ |__/  \__/       \______/ |__/  |__/|__/  |__/   |__/   \033[0m

                                                                              \033[38;5;220mCustom Chat Tool\033[0m
                                                                      \033[38;5;220mhttps://github.com/superchimpy1-ctrl\033[0m

"""
    Clear()
    print(logo)

if __name__ == "__main__":
    main()


def gui(func, *args):
    """Schedule a GUI call on the main thread (tkinter is not thread-safe)."""
    try:
        root.after(0, func, *args)
    except Exception:
        pass  # Window already destroyed


def update_status(message):
    status_label.config(
        text=message,
        fg=ACCENT_GREEN if scanning_enabled else ACCENT_RED
    )


def round_rectangle(canvas, x1, y1, x2, y2, radius=18, **kwargs):
    """Draws a rounded rectangle on a Canvas and returns its item id."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ---- Trigger handling ----
def send_phrase(ch):
    """Open chat, type the phrase, and submit. Runs on a worker thread."""
    global is_typing
    phrase = phrases.get(ch, "")
    if not phrase:
        gui(log_message, f"No phrase set for '{ch}'")
        return
    is_typing = True
    try:
        chat_key = chat_keys.get(ch, "t")
        keyboard.press(chat_key)
        keyboard.release(chat_key)
        time.sleep(CHAT_OPEN_DELAY)
        keyboard.type(phrase)
        time.sleep(SUBMIT_DELAY)
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        gui(log_message, f"Sent '{ch}' phrase: {phrase.strip()}")
    except Exception as e:
        gui(log_message, f"Error sending phrase: {e}")
    finally:
        is_typing = False


def try_trigger(ch):
    """Fire a phrase if allowed. Returns True if the trigger was accepted."""
    global last_trigger_time
    if not scanning_enabled or is_typing or gui_focused:
        return False
    now = time.time()
    if now - last_trigger_time < TRIGGER_COOLDOWN:
        return False
    last_trigger_time = now
    # Worker thread so we never block the keyboard hook with our sleeps
    threading.Thread(target=send_phrase, args=(ch,), daemon=True).start()
    return True


def on_press(key):
    global scanning_enabled
    try:
        if key == Key.f6:
            scanning_enabled = True
            gui(update_status, "Scanning: Enabled")
            gui(log_message, "Scanning enabled (F6)")
        elif key == Key.f7:
            scanning_enabled = False
            gui(update_status, "Scanning: Disabled")
            gui(log_message, "Scanning disabled (F7)")
        elif not (WINDOWS and suppress_keys):
            # Suppression off: triggers are handled here instead of the win32 filter
            ch = (getattr(key, "char", None) or "").lower()
            if ch in TRIGGER_KEYS:
                try_trigger(ch)
    except Exception:
        pass


def win32_event_filter(msg, data):
    """Swallow trigger keys system-wide when they fire, so the game never sees them."""
    if not suppress_keys:
        return True
    if msg not in (WM_KEYDOWN, WM_SYSKEYDOWN):
        return True
    if data.flags & LLKHF_INJECTED:
        return True  # Our own synthetic keystrokes — never touch these
    ch = VK_MAP.get(data.vkCode)
    if ch and try_trigger(ch):
        listener.suppress_event()
    return True


# ---- GUI main window ----
root = tk.Tk()
root.title("Rocket League Quick Chat Tool")
root.geometry("780x680")
root.configure(bg=BG_MAIN)
root.resizable(False, False)


def on_focus_in(event):
    global gui_focused
    gui_focused = True


def on_focus_out(event):
    global gui_focused
    gui_focused = False


root.bind("<FocusIn>", on_focus_in)
root.bind("<FocusOut>", on_focus_out)

# ---- Header ----
header_frame = tk.Frame(root, bg=BG_MAIN)
header_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 5), sticky="w")

tk.Label(
    header_frame, text="🎮 Rocket League Quick Chat Tool",
    font=FONT_TITLE, fg=FG_TEXT, bg=BG_MAIN
).pack(anchor="w")

tk.Label(
    header_frame, text="Press F6 to Enable  •  Press F7 to Disable  •  Leave a space before phrases",
    font=FONT_SUB, fg=FG_SUBTEXT, bg=BG_MAIN
).pack(anchor="w", pady=(4, 0))

# ---- Divider ----
tk.Frame(root, bg=BORDER_COLOR, height=1).grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(15, 15))

# ---- Phrase input panel (rounded) ----
PANEL_W, PANEL_H = 740, 210
panel_canvas = tk.Canvas(root, width=PANEL_W, height=PANEL_H, bg=BG_MAIN, highlightthickness=0)
panel_canvas.grid(row=2, column=0, columnspan=2, padx=20, pady=5)
round_rectangle(panel_canvas, 0, 0, PANEL_W, PANEL_H, radius=32, fill=BG_PANEL, outline=BORDER_COLOR, width=1)

ENTRY_RADIUS = 20
ENTRY_H = 46
ENTRY_W = 370


def make_phrase_row(canvas, y_center, key_label, default_phrase="", default_chat="Team"):
    canvas.create_text(
        30, y_center, anchor="w",
        text=f"Phrase for '{key_label}':",
        font=FONT_LABEL, fill=FG_TEXT
    )

    ex1, ey1 = 210, y_center - ENTRY_H // 2
    ex2, ey2 = ex1 + ENTRY_W, ey1 + ENTRY_H
    round_rectangle(
        canvas, ex1, ey1, ex2, ey2,
        radius=ENTRY_RADIUS, fill=BG_ENTRY, outline=BORDER_COLOR, width=1
    )

    entry = tk.Entry(
        canvas, font=FONT_MAIN,
        bg=BG_ENTRY, fg=FG_TEXT, insertbackground=FG_TEXT,
        relief="flat", highlightthickness=0, borderwidth=0
    )
    if default_phrase:
        entry.insert(0, default_phrase)
    # Inset the entry within the rounded rect so its square corners
    # stay hidden under the curve.
    canvas.create_window(
        ex1 + ENTRY_RADIUS, y_center,
        window=entry, anchor="w",
        width=ENTRY_W - 2 * ENTRY_RADIUS, height=ENTRY_H - 10
    )

    # Team/All chat selector
    var = tk.StringVar(value=default_chat)
    option = tk.OptionMenu(canvas, var, "Team", "All")
    option.config(
        bg=BG_ENTRY, fg=FG_TEXT, activebackground=BG_PANEL,
        activeforeground=FG_TEXT, relief="flat",
        highlightthickness=0, borderwidth=0, font=FONT_MAIN
    )
    option["menu"].config(bg=BG_ENTRY, fg=FG_TEXT, font=FONT_MAIN)
    canvas.create_window(
        ex2 + 15, y_center, window=option, anchor="w",
        width=110, height=ENTRY_H - 10
    )
    return entry, var


phrase_v_entry, chat_v_var = make_phrase_row(
    panel_canvas, 55, "v",
    default_phrase=saved_config["phrases"]["v"], default_chat=saved_config["chat_keys"]["v"]
)
phrase_r_entry, chat_r_var = make_phrase_row(
    panel_canvas, 105, "r",
    default_phrase=saved_config["phrases"]["r"], default_chat=saved_config["chat_keys"]["r"]
)
phrase_f_entry, chat_f_var = make_phrase_row(
    panel_canvas, 155, "f",
    default_phrase=saved_config["phrases"]["f"], default_chat=saved_config["chat_keys"]["f"]
)

# ---- Status ----
status_label = tk.Label(
    root, text="Scanning: Disabled",
    font=FONT_LABEL, fg=ACCENT_RED, bg=BG_MAIN
)
status_label.grid(row=3, column=0, columnspan=2, padx=20, pady=(15, 2))

# ---- Suppress checkbox ----
suppress_var = tk.BooleanVar(value=True)


def update_suppress():
    global suppress_keys
    suppress_keys = suppress_var.get()


suppress_check = tk.Checkbutton(
    root, text="Suppress trigger keys (v/r/f won't reach the game when they fire)",
    variable=suppress_var, command=update_suppress,
    bg=BG_MAIN, fg=FG_SUBTEXT, selectcolor=BG_ENTRY,
    activebackground=BG_MAIN, activeforeground=FG_TEXT,
    font=FONT_SUB, highlightthickness=0
)
suppress_check.grid(row=4, column=0, columnspan=2, padx=20, pady=(0, 8))
if not WINDOWS:
    suppress_var.set(False)
    suppress_keys = False
    suppress_check.config(state="disabled", text="Suppress trigger keys (Windows only)")

# ---- Log (rounded) ----
LOG_W, LOG_H = 740, 170
LOG_RADIUS = 32
LOG_INSET = 16

log_canvas = tk.Canvas(root, width=LOG_W, height=LOG_H, bg=BG_MAIN, highlightthickness=0)
log_canvas.grid(row=5, column=0, columnspan=2, padx=20, pady=5)
round_rectangle(log_canvas, 0, 0, LOG_W, LOG_H, radius=LOG_RADIUS, fill=BG_LOG, outline=BORDER_COLOR, width=1)

log_text = scrolledtext.ScrolledText(
    log_canvas,
    bg=BG_LOG, fg=FG_SUBTEXT, insertbackground=FG_TEXT,
    font=("Consolas", 9), relief="flat",
    highlightthickness=0, borderwidth=0
)
log_canvas.create_window(
    LOG_INSET, LOG_INSET,
    window=log_text, anchor="nw",
    width=LOG_W - 2 * LOG_INSET, height=LOG_H - 2 * LOG_INSET
)


def log_message(msg):
    log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
    log_text.see(tk.END)


# ---- Start / Stop ----
def start_listener():
    global listener, scanning_enabled

    # Snapshot GUI values into plain dicts (safe to read from listener threads)
    phrases["v"] = phrase_v_entry.get()
    phrases["r"] = phrase_r_entry.get()
    phrases["f"] = phrase_f_entry.get()
    chat_keys["v"] = "t" if chat_v_var.get() == "Team" else "y"
    chat_keys["r"] = "t" if chat_r_var.get() == "Team" else "y"
    chat_keys["f"] = "t" if chat_f_var.get() == "Team" else "y"

    save_config()
    log_message(f"Saved phrases to {os.path.basename(CONFIG_FILE)}")

    # Stop previous listener if it exists
    if listener is not None:
        try:
            listener.stop()
            log_message("Previous listener stopped")
        except Exception:
            pass

    # Reset state
    scanning_enabled = False
    update_status("Scanning: Disabled")
    log_message("Resetting configuration...")

    # Platform-prefixed kwargs are ignored on other platforms
    listener = Listener(on_press=on_press, win32_event_filter=win32_event_filter)
    listener.start()

    log_message("✓ Listener started | Press F6 to enable | F7 to disable")
    root.after(1000, lambda: messagebox.showinfo(
        "Ready",
        "Press F6 to enable scanning!\n\n"
        "v → [chat][Phrase v]\n"
        "r → [chat][Phrase r]\n"
        "f → [chat][Phrase f]"
    ))


def stop_program():
    global listener, scanning_enabled

    # Snapshot whatever is currently in the fields so edits aren't lost
    # even if "Start Listening" was never clicked.
    phrases["v"] = phrase_v_entry.get()
    phrases["r"] = phrase_r_entry.get()
    phrases["f"] = phrase_f_entry.get()
    chat_keys["v"] = "t" if chat_v_var.get() == "Team" else "y"
    chat_keys["r"] = "t" if chat_r_var.get() == "Team" else "y"
    chat_keys["f"] = "t" if chat_f_var.get() == "Team" else "y"
    save_config()

    if listener is not None:
        try:
            listener.stop()
        except Exception:
            pass

    scanning_enabled = False
    root.destroy()


# Stop the listener even when the window is closed with the X button
root.protocol("WM_DELETE_WINDOW", stop_program)

# ---- Rounded buttons ----
BTN_W, BTN_H = 210, 50
BTN_RADIUS = 25


def make_rounded_button(canvas, x, label, command, fill, hover_fill):
    rect = round_rectangle(
        canvas, x, 0, x + BTN_W, BTN_H,
        radius=BTN_RADIUS, fill=fill, outline=""
    )
    text = canvas.create_text(
        x + BTN_W // 2, BTN_H // 2,
        text=label, font=FONT_LABEL, fill="#0e0e0e"
    )

    def on_click(event):
        command()

    def on_enter(event):
        canvas.itemconfig(rect, fill=hover_fill)
        canvas.config(cursor="hand2")

    def on_leave(event):
        canvas.itemconfig(rect, fill=fill)

    for item in (rect, text):
        canvas.tag_bind(item, "<Button-1>", on_click)
        canvas.tag_bind(item, "<Enter>", on_enter)
        canvas.tag_bind(item, "<Leave>", on_leave)


button_canvas = tk.Canvas(
    root, width=BTN_W * 2 + 20, height=BTN_H, bg=BG_MAIN, highlightthickness=0
)
button_canvas.grid(row=6, column=0, columnspan=2, padx=20, pady=(15, 20))

make_rounded_button(button_canvas, 0, "▶  Start Listening", start_listener, ACCENT_GREEN, "#2fbf6f")
make_rounded_button(button_canvas, BTN_W + 20, "■  Stop & Exit", stop_program, ACCENT_RED, "#e04b4b")

log_message("Ready. Press 'Start Listening' to begin.")

root.mainloop()