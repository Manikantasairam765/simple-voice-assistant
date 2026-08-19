"""Jarvis desktop voice assistant with a Tkinter interface.
"""

import datetime
import math
import os
import queue
import shutil
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext

import pyjokes
import pyttsx3
import pywhatkit
import speech_recognition as sr
import wikipedia


BG = "#0b1020"
PANEL = "#151d35"
ACCENT = "#47d7ff"
BLUE = "#6aa9ff"
TEXT = "#eaf2ff"
MUTED = "#9fb0cf"
SUCCESS = "#74e6a2"
HOVER = "#263b68"
GLOW = "#143151"


class JarvisApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("JARVIS — Voice Assistant")
        self.root.geometry("780x600")
        self.root.minsize(620, 480)
        self.root.configure(bg=BG)

        self.speech_queue: queue.Queue[str | None] = queue.Queue()
        self.busy = False
        self.closing = False
        self.pulse_step = 0
        self.quick_buttons: list[tk.Button] = []
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)
        self._choose_voice()
        threading.Thread(target=self._speech_worker, daemon=True).start()

        self._build_ui()
        self.log("Jarvis", "Online. Press Listen or type a command.")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._animate_interface()

    def _choose_voice(self) -> None:
        """Prefer an English voice, while retaining the system default if unavailable."""
        for voice in self.engine.getProperty("voices"):
            details = f"{voice.name} {voice.id}".lower()
            if "english" in details or "zira" in details or "david" in details:
                self.engine.setProperty("voice", voice.id)
                return

    def _build_ui(self) -> None:
        self._build_dashboard()
        return
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=34, pady=(28, 12))
        self.clock = tk.Label(header, font=("Consolas", 12, "bold"), fg=TEXT, bg=BG)
        self.clock.pack(anchor="e", side="right", pady=10)
        tk.Label(header, text="JARVIS", font=("Segoe UI", 28, "bold"), fg=ACCENT, bg=BG).pack(anchor="w")
        self.status = tk.Label(header, text="● READY", font=("Segoe UI", 10, "bold"), fg=SUCCESS, bg=BG)
        self.status.pack(anchor="w", pady=(2, 0))

        commands = tk.Label(
            self.root,
            text="Try: open Google · play Blinding Lights · who is Ada Lovelace · joke · time · exit",
            font=("Segoe UI", 10), fg=MUTED, bg=BG, wraplength=700, justify="left",
        )
        commands.pack(fill="x", padx=34, pady=(0, 14))

        quick_actions = tk.Frame(self.root, bg=BG)
        quick_actions.pack(fill="x", padx=34, pady=(0, 14))
        for label, command in (("TIME", "time"), ("JOKE", "joke"), ("GOOGLE", "open google"), ("YOUTUBE", "open youtube"), ("HELP", "help")):
            button = tk.Button(quick_actions, text=label, command=lambda value=command: self._quick_command(value), bg=GLOW, fg=ACCENT, activebackground=HOVER, activeforeground=TEXT, relief="flat", bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=14, pady=7)
            button.pack(side="left", padx=(0, 8))
            self._add_hover(button, GLOW, HOVER)
            self.quick_buttons.append(button)

        self.history = scrolledtext.ScrolledText(
            self.root, height=17, bg=PANEL, fg=TEXT, insertbackground=TEXT,
            font=("Segoe UI", 11), wrap="word", relief="flat", padx=16, pady=14,
            state="disabled",
        )
        self.history.pack(fill="both", expand=True, padx=34)
        self.history.tag_configure("jarvis", foreground=ACCENT, font=("Segoe UI", 11, "bold"))
        self.history.tag_configure("you", foreground=SUCCESS, font=("Segoe UI", 11, "bold"))

        controls = tk.Frame(self.root, bg=BG)
        controls.pack(fill="x", padx=34, pady=20)
        self.entry = tk.Entry(
            controls, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat",
            font=("Segoe UI", 12),
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 10))
        self.entry.bind("<Return>", lambda _event: self.submit_text())
        tk.Button(
            controls, text="SEND", command=self.submit_text, bg="#213158", fg=TEXT,
            activebackground="#2a3f71", activeforeground=TEXT, relief="flat",
            font=("Segoe UI", 10, "bold"), padx=18, pady=10,
        ).pack(side="left", padx=(0, 10))
        self.listen_button = tk.Button(
            controls, text="◉  LISTEN", command=self.listen, bg=ACCENT, fg="#06101e",
            activebackground="#8be9ff", relief="flat", font=("Segoe UI", 10, "bold"),
            padx=18, pady=10,
        )
        self.listen_button.pack(side="left")
        self.listen_button.configure(cursor="hand2")
        self._add_hover(self.listen_button, ACCENT, "#8be9ff", "#06101e")
        self.entry.focus_set()

    def _panel(self, parent: tk.Widget, title: str) -> tk.Frame:
        panel = tk.Frame(parent, bg="#091b2d", highlightbackground="#164765", highlightthickness=1)
        tk.Label(panel, text=title, bg="#091b2d", fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(9, 5))
        return panel

    def _build_dashboard(self) -> None:
        self.root.geometry("1200x730")
        self.root.minsize(1000, 650)
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True, padx=8, pady=8)

        sidebar = tk.Frame(shell, bg="#071827", width=178, highlightbackground="#164765", highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 10)); sidebar.pack_propagate(False)
        tk.Label(sidebar, text="◉  JARVIS", bg="#0a3650", fg=TEXT, font=("Segoe UI", 15, "bold"), pady=15).pack(fill="x")
        tk.Label(sidebar, text="COMMAND CENTER", bg="#0a3650", fg=ACCENT, font=("Segoe UI", 6, "bold")).pack(fill="x", pady=(0, 13))
        for label, command in (("▧   Calendar", "date"),):
            button = tk.Button(sidebar, text=label, command=lambda value=command: self._quick_command(value), anchor="w", bg="#071827", fg=TEXT, activebackground=HOVER, activeforeground=ACCENT, relief="flat", bd=0, font=("Segoe UI", 9), cursor="hand2", padx=14, pady=9)
            button.pack(fill="x", padx=5, pady=1); self._add_hover(button, "#071827", "#103451")
        self.voice_label = tk.Label(sidebar, text="VOICE STATUS\n\n||||||||||||||||\n\nREADY TO LISTEN", justify="center", bg="#09263b", fg=ACCENT, font=("Consolas", 9, "bold"), pady=15)
        self.voice_label.pack(side="bottom", fill="x", padx=10, pady=12)

        main = tk.Frame(shell, bg=BG); main.pack(side="left", fill="both", expand=True)
        header = tk.Frame(main, bg="#071827", highlightbackground="#164765", highlightthickness=1, height=46); header.pack(fill="x", pady=(0, 10)); header.pack_propagate(False)
        self.status = tk.Label(header, text="●  SYSTEM STATUS  •  OPTIMAL", bg="#071827", fg=SUCCESS, font=("Segoe UI", 8, "bold")); self.status.pack(side="left", padx=18)
        title = tk.Frame(header, bg="#071827"); title.pack(side="left", expand=True)
        tk.Label(title, text="Monday, 15 June 2026", bg="#071827", fg=TEXT, font=("Segoe UI", 7, "bold")).pack()
        self.clock = tk.Label(title, bg="#071827", fg=ACCENT, font=("Segoe UI", 15, "bold")); self.clock.pack()
        tk.Label(header, text="⌕  Search...     ◫   ♧   ⚙", bg="#071827", fg=MUTED, font=("Segoe UI", 9)).pack(side="right", padx=16)

        top = tk.Frame(main, bg=BG); top.pack(fill="both", expand=True, pady=(0, 10))
        overview = self._panel(top, "AI CORE OVERVIEW"); overview.pack(side="left", fill="y", padx=(0, 10))
        for item, value, color in (("AI Core", "Active", ACCENT), ("Memory", "3,380 Stored", BLUE), ("Voice", "Online", SUCCESS), ("Agents", "2 Running", "#be7cff"), ("System", "Optimal", SUCCESS)):
            row = tk.Label(overview, text=f"  {item}\n     {value}", justify="left", bg="#0d2940", fg=color, font=("Segoe UI", 8, "bold"), padx=10, pady=6)
            row.pack(fill="x", padx=9, pady=3)
        feed = self._panel(top, "LIVE INTELLIGENCE FEED"); feed.pack(side="right", fill="y", padx=(10, 0))
        for item in ("Design review scheduled", "2 tasks are overdue", "Pull requests awaiting review", "Your focus block is active", "CPU usage at 15%"):
            tk.Label(feed, text="●  "+item, anchor="w", bg="#0d2940", fg=TEXT, font=("Segoe UI", 8), padx=8, pady=7).pack(fill="x", padx=8, pady=3)
        core_panel = self._panel(top, "JARVIS // AI CORE"); core_panel.pack(side="left", fill="both", expand=True)
        self.core = tk.Canvas(core_panel, bg="#071827", highlightthickness=0, height=250); self.core.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.core.bind("<Button-1>", lambda _event: self.listen()); self.core.bind("<Enter>", lambda _event: self.core.configure(cursor="hand2")); self.core.bind("<Leave>", lambda _event: self.core.configure(cursor=""))

        middle = tk.Frame(main, bg=BG); middle.pack(fill="x", pady=(0, 10))
        agents = self._panel(middle, "ACTIVE AGENTS"); agents.pack(side="left", fill="both", expand=True, padx=(0, 5))
        for label in ("</> Coding Agent\nActive", "⌕ Research Agent\nActive", "▤ Memory Agent\nStandby", "◉ System Agent\nOnline"):
            tk.Label(agents, text=label, justify="left", bg="#0d2940", fg=SUCCESS, font=("Segoe UI", 8, "bold"), padx=10, pady=8).pack(side="left", fill="both", expand=True, padx=4, pady=(0, 9))
        quick = self._panel(middle, "QUICK COMMANDS"); quick.pack(side="right", padx=(5, 0))
        for label, command in (("◫  Open Calendar", "date"),):
            button = tk.Button(quick, text=label, command=lambda value=command: self._quick_command(value), anchor="w", bg="#0d2940", fg=TEXT, activebackground=HOVER, relief="flat", bd=0, font=("Segoe UI", 8), cursor="hand2", padx=9, pady=5)
            button.pack(fill="x", padx=8, pady=2); self._add_hover(button, "#0d2940", HOVER)

        bottom = tk.Frame(main, bg=BG); bottom.pack(fill="both", expand=True)
        history_panel = self._panel(bottom, "JARVIS // CONVERSATION LOG"); history_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.history = scrolledtext.ScrolledText(history_panel, height=9, bg="#071827", fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 10), wrap="word", relief="flat", padx=12, pady=8, state="disabled")
        self.history.pack(fill="both", expand=True, padx=7, pady=(0, 7)); self.history.tag_configure("jarvis", foreground=ACCENT, font=("Segoe UI", 10, "bold")); self.history.tag_configure("you", foreground=SUCCESS, font=("Segoe UI", 10, "bold"))
        monitor = self._panel(bottom, "SYSTEM MONITOR"); monitor.pack(side="right", fill="y", padx=(5, 0))
        tk.Label(monitor, text="CPU   15%\n\nRAM   54%\n\nDISK  40%", justify="left", bg="#091b2d", fg=ACCENT, font=("Consolas", 10, "bold"), padx=24, pady=16).pack()

        dock = tk.Frame(main, bg="#071827", highlightbackground="#164765", highlightthickness=1); dock.pack(fill="x", pady=(10, 0))
        tk.Label(dock, text="VOICE COMMAND", bg="#071827", fg=ACCENT, font=("Segoe UI", 8, "bold")).pack(side="left", padx=14)
        self.entry = tk.Entry(dock, bg="#0d2940", fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10)); self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=8, pady=7); self.entry.bind("<Return>", lambda _event: self.submit_text())
        send = tk.Button(dock, text="EXECUTE", command=self.submit_text, bg="#123a61", fg=TEXT, activebackground=HOVER, relief="flat", font=("Segoe UI", 8, "bold"), cursor="hand2", padx=14, pady=7); send.pack(side="left", padx=5); self._add_hover(send, "#123a61", HOVER)
        self.listen_button = tk.Button(dock, text="TALK TO JARVIS", command=self.listen, bg=ACCENT, fg="#06101e", activebackground="#8be9ff", relief="flat", font=("Segoe UI", 8, "bold"), cursor="hand2", padx=14, pady=7); self.listen_button.pack(side="left", padx=(0, 8)); self._add_hover(self.listen_button, ACCENT, "#8be9ff", "#06101e")
        self.entry.focus_set()

    def _draw_core(self) -> None:
        if not hasattr(self, "core"):
            return
        canvas = self.core; canvas.delete("all"); width, height = max(canvas.winfo_width(), 300), max(canvas.winfo_height(), 200); x, y = width//2, height//2
        for gx in range(18, width, 28):
            for gy in range(18, height, 28): canvas.create_oval(gx, gy, gx+1, gy+1, fill="#195070", outline="")
        pulse = 4 + int(3 * math.sin(self.pulse_step / 2)); radius = min(height//2-20, 88) + pulse
        for angle in range(0, 360, 30):
            rad = math.radians(angle+self.pulse_step*4); ex, ey = x+math.cos(rad)*(radius+34), y+math.sin(rad)*(radius+20); canvas.create_line(x, y, ex, ey, fill="#164b6b")
        canvas.create_oval(x-radius, y-radius, x+radius, y+radius, outline=ACCENT, width=2); canvas.create_oval(x-radius+13, y-radius+13, x+radius-13, y+radius-13, outline="#237cc4", width=1)
        canvas.create_arc(x-radius-26, y-radius-26, x+radius+26, y+radius+26, start=self.pulse_step*8, extent=110, style="arc", outline=ACCENT, width=3)
        canvas.create_text(x, y-12, text="J A R V I S", fill=ACCENT, font=("Segoe UI", 21, "bold")); canvas.create_text(x, y+18, text="AI CORE", fill=TEXT, font=("Segoe UI", 10, "bold")); canvas.create_text(x, y+39, text="CLICK TO SPEAK", fill=SUCCESS if not self.busy else ACCENT, font=("Segoe UI", 8, "bold"))

    def _add_hover(self, widget: tk.Button, normal: str, hovered: str, text_color: str | None = None) -> None:
        """Give standard Tk buttons a consistent pointer hover state."""
        widget.bind("<Enter>", lambda _event: widget.configure(bg=hovered, fg=text_color or TEXT))
        widget.bind("<Leave>", lambda _event: widget.configure(bg=normal, fg=text_color or (ACCENT if normal == GLOW else TEXT)))

    def _quick_command(self, command: str) -> None:
        if command == "help":
            self.speak("Try asking for the time, a joke, a Wikipedia topic, or opening Google, YouTube, ChatGPT, or Instagram.")
            return
        self.handle_command(command)

    def _animate_interface(self) -> None:
        if self.closing:
            return
        self.pulse_step = (self.pulse_step + 1) % 18
        if not self.busy:
            self.status.configure(fg=SUCCESS if self.pulse_step < 9 else "#4abf82")
        self.clock.configure(text=datetime.datetime.now().strftime("%d %b  %H:%M:%S"))
        self.voice_label.configure(text="VOICE STATUS\n\n" + ("|*|*|*|*|*|*|" if self.busy else "|||||||||       ") + "\n\n" + ("LISTENING..." if self.busy else "READY TO LISTEN"))
        self._draw_core()
        self.root.after(180, self._animate_interface)

    def log(self, speaker: str, message: str) -> None:
        if self.closing:
            return
        tag = "jarvis" if speaker == "Jarvis" else "you"
        self.history.configure(state="normal")
        self.history.insert("end", f"{speaker}: ", tag)
        self.history.insert("end", f"{message}\n\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def set_status(self, text: str, color: str) -> None:
        if not self.closing:
            self.status.configure(text=text, fg=color)

    def speak(self, message: str) -> None:
        self.log("Jarvis", message)
        self.speech_queue.put(message)

    def _speech_worker(self) -> None:
        while True:
            message = self.speech_queue.get()
            if message is None:
                return
            try:
                self.engine.say(message)
                self.engine.runAndWait()
            except RuntimeError:
                pass

    def submit_text(self) -> None:
        command = self.entry.get().strip()
        if command:
            self.entry.delete(0, "end")
            self.handle_command(command)

    def listen(self) -> None:
        if self.busy:
            return
        self.busy = True
        self.listen_button.configure(state="disabled")
        self.set_status("● LISTENING…", ACCENT)
        threading.Thread(target=self._recognize_voice, daemon=True).start()

    def _recognize_voice(self) -> None:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.7)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=9)
            command = recognizer.recognize_google(audio)
            self.root.after(0, lambda: self.handle_command(command))
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.speak("I did not hear anything. Please try again."))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.speak("I could not understand that. Please try again."))
        except OSError:
            self.root.after(0, lambda: self.speak("I cannot access your microphone. Check that it is connected and allowed."))
        except Exception as error:
            self.root.after(0, lambda: self.speak(f"Voice recognition error: {error}"))
        finally:
            self.root.after(0, self._finish_listening)

    def _finish_listening(self) -> None:
        self.busy = False
        self.listen_button.configure(state="normal")
        self.set_status("● READY", SUCCESS)

    def handle_command(self, raw_command: str) -> None:
        command = raw_command.lower().strip()
        self.log("You", raw_command)
        self.set_status("● WORKING…", ACCENT)
        threading.Thread(target=self._run_command, args=(command,), daemon=True).start()

    def _respond(self, message: str) -> None:
        self.root.after(0, lambda: self.speak(message))

    def _run_command(self, command: str) -> None:
        try:
            websites = {
                "open google": ("Google", "https://www.google.com"),
                "open youtube": ("YouTube", "https://www.youtube.com"),
                "open chatgpt": ("ChatGPT", "https://chatgpt.com"),
                "open instagram": ("Instagram", "https://www.instagram.com"),
            }
            for trigger, (name, url) in websites.items():
                if trigger in command:
                    webbrowser.open(url)
                    self._respond(f"Opening {name}.")
                    return

            if command in {"time", "what time is it", "tell me the time"} or "current time" in command:
                self._respond("The current time is " + datetime.datetime.now().strftime("%I:%M %p"))
            elif command in {"date", "what is the date", "tell me the date"} or "today's date" in command:
                self._respond("Today's date is " + datetime.datetime.now().strftime("%d %B %Y"))
            elif command.startswith("play "):
                song = command[5:].strip()
                if song:
                    self._respond(f"Playing {song} on YouTube.")
                    pywhatkit.playonyt(song)
                else:
                    self._respond("Please tell me the song name.")
            elif command.startswith("who is ") or command.startswith("what is "):
                topic = command.split(" is ", 1)[1].strip()
                try:
                    summary = wikipedia.summary(topic, sentences=2, auto_suggest=False)
                    self._respond(summary)
                except wikipedia.exceptions.DisambiguationError as error:
                    self._respond(f"There are several results for {topic}. Please be more specific, for example {error.options[0]}.")
                except wikipedia.exceptions.PageError:
                    self._respond(f"I could not find information about {topic}.")
            elif "joke" in command:
                self._respond(pyjokes.get_joke())
            elif "open code" in command or "open visual studio code" in command:
                self._open_vscode()
            elif command in {"hello", "hi", "hey jarvis"}:
                self._respond("Hello. How can I help you?")
            elif "how are you" in command:
                self._respond("I am running perfectly. Thank you for asking.")
            elif command in {"exit", "stop", "bye", "quit"} or command.startswith("exit "):
                self._respond("Goodbye. Have a nice day.")
                self.root.after(1800, self.close)
            else:
                self._respond("I did not understand that command. Try opening a website, playing a song, asking who someone is, or asking for the time.")
        except Exception as error:
            self._respond(f"Sorry, that command failed: {error}")
        finally:
            self.root.after(0, lambda: self.set_status("● READY", SUCCESS))

    def _open_vscode(self) -> None:
        code = shutil.which("code")
        standard_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe"
        try:
            if code:
                os.startfile(code)
            elif standard_path.is_file():
                os.startfile(str(standard_path))
            else:
                raise FileNotFoundError
            self._respond("Opening Visual Studio Code.")
        except FileNotFoundError:
            self._respond("Visual Studio Code was not found. Install it, or add the code command to your system path.")

    def close(self) -> None:
        if self.closing:
            return
        self.closing = True
        self.speech_queue.put(None)
        self.root.after(100, self.root.destroy)


if __name__ == "__main__":
    window = tk.Tk()
    JarvisApp(window)
    window.mainloop()
