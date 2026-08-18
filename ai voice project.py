import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import tkinter as tk
import sounddevice as sd
import subprocess
from threading import Thread
from urllib.parse import quote_plus

# ---------------- INIT ----------------
engine = pyttsx3.init()
engine.setProperty("rate", 170)

recognizer = sr.Recognizer()
running = False

# ---------------- SPEAK ----------------
def speak(text):
    engine.say(text)
    engine.runAndWait()

# ---------------- UI SAFE UPDATES ----------------
def set_status(text, color="#00ADB5"):
    root.after(0, lambda: status_label.config(text=text, fg=color))

def set_output(text):
    root.after(0, lambda: output_label.config(text=text))

def open_web(query):
    """Open a spoken website address or run an accurately encoded web search."""
    query = query.strip().lower()
    if not query:
        speak("Please say what you want to search for")
        return

    site = query.replace(" dot ", ".").replace(" slash ", "/").replace(" ", "")
    if "." in site and " " not in query.replace(" dot ", ""):
        url = site if site.startswith(("http://", "https://")) else f"https://{site}"
        speak(f"Opening {query}")
    else:
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        speak(f"Searching the web for {query}")

    set_output(f"Opening: {url}")
    webbrowser.open_new_tab(url)

def open_application(command):
    """Launch supported Windows programs from a spoken command."""
    apps = {
        "notepad": ("notepad.exe", "Opening Notepad"),
        "calculator": ("calc.exe", "Opening Calculator"),
        "calc": ("calc.exe", "Opening Calculator"),
        "file explorer": ("explorer.exe", "Opening File Explorer"),
        "explorer": ("explorer.exe", "Opening File Explorer"),
        "command prompt": ("cmd.exe", "Opening Command Prompt"),
        "terminal": ("wt.exe", "Opening Terminal"),
        "settings": ("ms-settings:", "Opening Settings"),
    }

    for name, (program, message) in apps.items():
        if name in command:
            try:
                subprocess.Popen([program])
                set_output(message)
                speak(message)
            except OSError:
                set_output(f"Could not open {name}")
                speak(f"I could not open {name}")
            return True
    return False

# ---------------- LISTEN ----------------
def listen():
    try:
        device = sd.query_devices(kind="input")
        sample_rate = int(device["default_samplerate"])
        set_status("Listening...", "#00ADB5")
        recording = sd.rec(
            int(4 * sample_rate), samplerate=sample_rate, channels=1, dtype="int16"
        )
        sd.wait()
        audio = sr.AudioData(recording.tobytes(), sample_rate, 2)
    except sd.PortAudioError as error:
        set_status("Microphone unavailable", "#FF2E63")
        set_output(f"Microphone error: {error}")
        return None

    try:
        command = recognizer.recognize_google(audio).lower()
        set_output(command)
        return command
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        speak("Speech service is unavailable")
        return ""

# ---------------- ASSISTANT LOOP ----------------
def assistant_loop():
    speak("Assistant started")
    set_status("Running", "#00FFAB")

    while running:
        cmd = listen()
        if not running:
            break
        if cmd is None:
            break
        if not cmd:
            continue

        if cmd.startswith(("browse ", "search web for ", "look up ")):
            for prefix in ("browse ", "search web for ", "look up "):
                if cmd.startswith(prefix):
                    open_web(cmd[len(prefix):])
                    break
            continue

        if cmd.startswith(("open website ", "open site ")):
            prefix = "open website " if cmd.startswith("open website ") else "open site "
            open_web(cmd[len(prefix):])
            continue

        if cmd.startswith("open ") and open_application(cmd):
            continue

        # ▶ PLAY YOUTUBE
        if cmd.startswith("play"):
            song = cmd.replace("play", "").strip()
            if song:
                speak(f"Playing {song}")
                webbrowser.open_new_tab(
                    f"https://www.youtube.com/results?search_query={quote_plus(song)}"
                )
            continue

        # 🔍 GOOGLE SEARCH
        if cmd.startswith("search for"):
            query = cmd.replace("search for", "").strip()
            if query:
                speak(f"Searching for {query}")
                webbrowser.open_new_tab(
                    f"https://www.google.com/search?q={quote_plus(query)}"
                )
            continue

        # ⏰ TIME
        if "time" in cmd:
            speak(datetime.datetime.now().strftime("%I:%M %p"))
            continue

        # 🌐 OPEN GOOGLE
        if "open google" in cmd:
            speak("Opening Google")
            webbrowser.open_new_tab("https://www.google.com")
            continue

        if "open youtube" in cmd:
            speak("Opening YouTube")
            webbrowser.open_new_tab("https://www.youtube.com")
            continue

        if "open gmail" in cmd:
            speak("Opening Gmail")
            webbrowser.open_new_tab("https://mail.google.com")
            continue

        # 🛑 STOP
        if "stop" in cmd:
            stop()
            break

        # ❌ EXIT
        if "exit" in cmd or "close assistant" in cmd:
            exit_app()
            break

# ---------------- CONTROLS ----------------
def start():
    global running
    if not running:
        running = True
        Thread(target=assistant_loop, daemon=True).start()

def stop():
    global running
    running = False
    set_status("Stopped", "#FF2E63")
    speak("Assistant stopped")

def exit_app():
    global running
    running = False
    speak("Exiting assistant")
    root.after(500, root.destroy)

# ---------------- UI ----------------
root = tk.Tk()
root.title("AURA | Voice Assistant")
root.geometry("680x670")
root.configure(bg="#0B1020")
root.resizable(False, False)

card = tk.Frame(root, bg="#393E46")
card.place(relx=0.5, rely=0.5, anchor="center", width=360, height=320)

tk.Label(
    card,
    text="🎤 Voice Assistant",
    font=("Segoe UI", 18, "bold"),
    fg="#EEEEEE",
    bg="#393E46"
).pack(pady=15)

status_label = tk.Label(
    card,
    text="Idle",
    font=("Segoe UI", 12, "bold"),
    fg="#00ADB5",
    bg="#393E46"
)
status_label.pack()

output_label = tk.Label(
    card,
    text="Say a command...",
    font=("Segoe UI", 11),
    fg="#EEEEEE",
    bg="#222831",
    wraplength=300,
    padx=10,
    pady=10
)
output_label.pack(pady=15)

btn_frame = tk.Frame(card, bg="#393E46")
btn_frame.pack(pady=20)

tk.Button(
    btn_frame,
    text="▶ Start",
    font=("Segoe UI", 11, "bold"),
    bg="#00ADB5",
    fg="white",
    width=12,
    relief="flat",
    command=start
).grid(row=0, column=0, padx=10)

tk.Button(
    btn_frame,
    text="⏹ Stop",
    font=("Segoe UI", 11, "bold"),
    bg="#FF2E63",
    fg="white",
    width=12,
    relief="flat",
    command=stop
).grid(row=0, column=1, padx=10)

card.destroy()

BG = "#0B1020"
PANEL = "#141B33"
PANEL_2 = "#1B2545"
TEXT = "#F4F7FF"
MUTED = "#A8B3CF"
ACCENT = "#6C7CFF"
SUCCESS = "#39D9A9"

main = tk.Frame(root, bg=BG, padx=42, pady=32)
main.pack(fill="both", expand=True)

header = tk.Frame(main, bg=BG)
header.pack(fill="x")
tk.Label(header, text="AURA", font=("Segoe UI", 23, "bold"), fg=TEXT, bg=BG).pack(side="left")
tk.Frame(main, bg=BG, height=18).pack(fill="x")

assistant_card = tk.Frame(main, bg=PANEL, padx=28, pady=24)
assistant_card.pack(fill="x")
status_row = tk.Frame(assistant_card, bg=PANEL)
status_row.pack(fill="x", pady=(4, 12))
tk.Label(status_row, text="●", font=("Segoe UI", 19), fg="#6B7697", bg=PANEL).pack(side="left")
status_label = tk.Label(status_row, text="Idle — press Start to begin", font=("Segoe UI", 14, "bold"), fg=MUTED, bg=PANEL)
status_label.pack(side="left", padx=(8, 0), pady=(2, 0))

output_label = tk.Label(assistant_card, text="", font=("Segoe UI", 11), fg=TEXT, bg=PANEL_2, wraplength=520, justify="left", anchor="w", padx=16, pady=22)
output_label.pack(fill="x")
status_label.config(text="")

btn_frame = tk.Frame(main, bg=BG)
btn_frame.pack(fill="x", pady=20)
tk.Button(btn_frame, text="START LISTENING", font=("Segoe UI", 11, "bold"), bg=ACCENT, activebackground="#8591FF", activeforeground="white", fg="white", padx=23, pady=12, bd=0, cursor="hand2", command=start).pack(side="left")
tk.Button(btn_frame, text="STOP", font=("Segoe UI", 11, "bold"), bg=PANEL_2, activebackground="#2A3760", activeforeground="white", fg=TEXT, padx=28, pady=12, bd=0, cursor="hand2", command=stop).pack(side="left", padx=12)

commands_card = tk.Frame(main, bg=PANEL, padx=24, pady=18)
commands_card.pack(fill="both", expand=True)
tk.Label(commands_card, text="TRY SAYING", font=("Segoe UI", 9, "bold"), fg=ACCENT, bg=PANEL).pack(anchor="w")
command_text = (
    "Browse latest technology news     •     Play lo-fi music\n"
    "Open Notepad     •     Search for Python tutorials\n"
    "Open website wikipedia dot org     •     What time is it?"
)
tk.Label(commands_card, text=command_text, font=("Segoe UI", 10), fg=MUTED, bg=PANEL, justify="left", anchor="w", padx=2, pady=12).pack(fill="x")

interactive_card = tk.Frame(main, bg=PANEL, padx=24, pady=18)
interactive_card.pack(fill="x", pady=(16, 0))
commands_card.pack_forget()

def submit_typed_search(event=None):
    query = search_var.get().strip()
    if query and query != "Type a web search or website...":
        search_var.set("")
        open_web(query)

def show_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    set_output(f"The time is {current_time}")
    speak(current_time)

def open_youtube():
    set_output("Opening YouTube")
    speak("Opening YouTube")
    webbrowser.open_new_tab("https://www.youtube.com")

def clear_transcript():
    set_output("")

search_row = tk.Frame(interactive_card, bg=PANEL)
search_row.pack(fill="x", pady=(10, 14))
search_var = tk.StringVar(value="Type a web search or website...")
search_entry = tk.Entry(search_row, textvariable=search_var, font=("Segoe UI", 10), fg=TEXT, bg=PANEL_2, insertbackground=TEXT, relief="flat", bd=0)
search_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
search_entry.bind("<FocusIn>", lambda event: search_var.set("") if search_var.get() == "Type a web search or website..." else None)
search_entry.bind("<Return>", submit_typed_search)
tk.Button(search_row, text="SEARCH", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white", activebackground="#8591FF", activeforeground="white", bd=0, padx=18, pady=9, cursor="hand2", command=submit_typed_search).pack(side="right")

quick_row = tk.Frame(interactive_card, bg=PANEL)
quick_row.pack(fill="x")
quick_button = {"font": ("Segoe UI", 9, "bold"), "bg": PANEL_2, "fg": TEXT, "activebackground": "#2A3760", "activeforeground": "white", "bd": 0, "padx": 13, "pady": 8, "cursor": "hand2"}
tk.Button(quick_row, text="NOTEPAD", command=lambda: open_application("open notepad"), **quick_button).pack(side="left")
tk.Button(quick_row, text="TIME", command=show_time, **quick_button).pack(side="left", padx=8)
tk.Button(quick_row, text="YOUTUBE", command=open_youtube, **quick_button).pack(side="left")
tk.Button(quick_row, text="CLEAR", command=clear_transcript, **quick_button).pack(side="right")

root.mainloop()
