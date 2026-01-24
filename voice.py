import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import tkinter as tk
from threading import Thread

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

# ---------------- LISTEN ----------------
def listen():
    with sr.Microphone() as source:
        set_status("Listening...", "#00ADB5")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
        except sr.WaitTimeoutError:
            return ""

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
        if not cmd:
            continue

        # ▶ PLAY YOUTUBE
        if cmd.startswith("play"):
            song = cmd.replace("play", "").strip()
            if song:
                speak(f"Playing {song}")
                webbrowser.open(
                    f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
                )
            continue

        # 🔍 GOOGLE SEARCH
        if cmd.startswith("search for"):
            query = cmd.replace("search for", "").strip()
            if query:
                speak(f"Searching for {query}")
                webbrowser.open(
                    f"https://www.google.com/search?q={query.replace(' ', '+')}"
                )
            continue

        # ⏰ TIME
        if "time" in cmd:
            speak(datetime.datetime.now().strftime("%I:%M %p"))
            continue

        # 🌐 OPEN GOOGLE
        if "open google" in cmd:
            speak("Opening Google")
            webbrowser.open("https://www.google.com")
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
root.title("Voice Assistant")
root.geometry("420x380")
root.configure(bg="#222831")
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

root.mainloop()
