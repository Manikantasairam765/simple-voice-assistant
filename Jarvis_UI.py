import datetime, math, queue, threading, webbrowser
import tkinter as tk
from urllib.parse import quote_plus

import pyjokes
import pyttsx3
import speech_recognition as sr
import wikipedia

BG, PANEL, CARD = '#050b14', '#081827', '#0b2134'
CYAN, BLUE, WHITE, MUTED, GREEN, RED = '#24dbff', '#258cff', '#ecf7ff', '#8aa8c1', '#30e6a1', '#ff6473'


class Jarvis:
    def __init__(self, root):
        self.r = root
        root.title('JARVIS | Command Center'); root.geometry('1365x760'); root.minsize(980, 650); root.configure(bg=BG)
        self.c = tk.Canvas(root, bg=BG, highlightthickness=0); self.c.pack(fill='both', expand=True)
        self.e = tk.Entry(root, bg='#071522', fg=WHITE, insertbackground=CYAN, relief='flat', font=('Segoe UI', 11), highlightthickness=0)
        self.e.bind('<Return>', lambda _: self.send()); self.e.bind('<FocusIn>', lambda _: self.set_hover('input')); self.e.bind('<FocusOut>', lambda _: self.set_hover(''))
        self.msg = 'Ready. Click the microphone or type a command.'
        self.logs = ['JARVIS: System online. Voice assistant ready.']
        self.hover = self.pressed = ''; self.listening = False; self.logs_visible = True; self.angle = self.frame = 0
        self.q = queue.Queue(); self.engine = pyttsx3.init(); self.engine.setProperty('rate', 175)
        threading.Thread(target=self.speaker, daemon=True).start()
        root.bind('<Configure>', lambda _: self.draw()); root.bind('<Escape>', lambda _: self.close())
        self.c.bind('<Button-1>', self.click); self.c.bind('<ButtonRelease-1>', lambda _: self.release()); self.c.bind('<Motion>', self.motion); self.c.bind('<Leave>', lambda _: self.set_hover(''))
        root.protocol('WM_DELETE_WINDOW', self.close); self.tick()

    def text(self, x, y, value, size=12, color=WHITE, bold=False, anchor='center'):
        self.c.create_text(x, y, text=value, fill=color, anchor=anchor, font=('Segoe UI', size, 'bold' if bold else 'normal'))

    def box(self, x1, y1, x2, y2, fill=PANEL, outline='#174365', width=1):
        return self.c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)

    def button(self, bounds, label, key, accent=CYAN):
        x1, y1, x2, y2 = bounds; active, down = self.hover == key, self.pressed == key
        if down: x1, y1, x2, y2 = x1 + 2, y1 + 2, x2 + 2, y2 + 2
        self.box(x1, y1, x2, y2, '#16425e' if down else '#103452' if active else '#0a1d2f', accent if active else '#1b4b69', 2 if active else 1)
        self.text((x1+x2)/2, (y1+y2)/2, label, 10, accent, True)

    def draw(self):
        c = self.c; c.delete('all'); w, h = max(self.r.winfo_width(), 980), max(self.r.winfo_height(), 650)
        left, right = 294, 310 if self.logs_visible else 26; cx, cy = (left+w-right)/2, h*.39
        # Navigation rail
        self.box(0, 0, 294, h, '#020a13', '#124363', 2); self.c.create_oval(28, 24, 68, 64, outline=CYAN, width=2)
        self.text(48, 44, 'J', 25, CYAN, True); self.text(91, 34, 'J A R V I S', 23, WHITE, True, 'w'); self.text(91, 59, 'COMMAND CENTER // ONLINE', 8, MUTED, True, 'w')
        self.button((25, 101, 270, 153), 'COMMAND CENTER', 'commands')
        for i, (name, index) in enumerate([('TIME & DATE', '01'), ('VOICE ASSISTANT', '02'), ('WEB & MUSIC', '03'), ('ALL COMMANDS', '04')]):
            y = 183+i*51; self.text(42, y, index, 9, CYAN, True); self.text(80, y, name, 11, WHITE, False, 'w'); c.create_line(29, y+25, 265, y+25, fill='#10324e')
        active = self.hover == 'mic' or self.listening
        self.box(28, h-218, 268, h-45, '#103653' if active else '#081a2b', CYAN if active else '#174365', 2)
        self.text(48, h-192, 'VOICE STATUS', 10, CYAN, True, 'w'); self.text(148, h-163, 'LISTENING...' if self.listening else 'READY TO LISTEN', 11, CYAN if self.listening else GREEN, True)
        pulse = int(7+5*math.sin(self.frame/3)) if self.listening else (5 if self.hover == 'mic' else 0)
        c.create_oval(96-pulse, h-137-pulse, 200+pulse, h-33+pulse, fill='#0a3050', outline=CYAN, width=3)
        self.text(148, h-87, 'MIC', 15, CYAN, True); self.text(148, h-57, 'TAP TO SPEAK', 9, MUTED, True)
        # Header
        self.box(left+16, 20, left+276, 68, '#071727', '#1c4d70'); self.text(left+37, 44, '*', 14, GREEN, True); self.text(left+60, 44, 'SYSTEM STATUS  •  OPTIMAL', 10, WHITE, True, 'w')
        self.text(cx, 31, datetime.datetime.now().strftime('%A, %d %B %Y'), 10, WHITE, True); self.text(cx, 56, datetime.datetime.now().strftime('%I:%M:%S %p'), 23, CYAN, True)
        self.button((w-275, 20, w-145, 68), 'HIDE LOGS' if self.logs_visible else 'SHOW LOGS', 'logs'); self.button((w-130, 20, w-25, 68), 'TERMINATE', 'exit', RED)
        # Animated visual core
        main_right = w-right; self.box(left+16, 88, main_right-18, h-235, '#061625', '#113d5b')
        for radius, color in ((154, '#082846'), (139, '#0a3152')): c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, fill=color, outline='')
        glow = 5 if self.hover == 'mic' else 0; c.create_oval(cx-122-glow, cy-122-glow, cx+122+glow, cy+122+glow, fill=BG, outline='#1e6792', width=2)
        c.create_arc(cx-111, cy-111, cx+111, cy+111, start=self.angle, extent=125, style='arc', outline=CYAN, width=4); c.create_arc(cx-91, cy-91, cx+91, cy+91, start=self.angle+180, extent=105, style='arc', outline=BLUE, width=3)
        c.create_oval(cx-4, cy-4, cx+4, cy+4, fill=CYAN, outline=''); self.text(cx, cy-15, 'J A R V I S', 25, CYAN, True); self.text(cx, cy+20, 'VOICE ASSISTANT', 11, WHITE, True); self.text(cx, cy+45, 'LISTENING' if self.listening else 'ONLINE', 10, CYAN if self.listening else GREEN, True)
        if self.logs_visible:
            x1, x2 = w-310, w-25; self.box(x1, 88, x2, h-235, CARD, '#174365'); self.text(x1+22, 115, 'JARVIS // ACTIVITY', 10, CYAN, True, 'w')
            for i, line in enumerate(self.logs[-5:]):
                y = 138+i*48; self.box(x1+22, y, x2-22, y+36, '#102b45', '#1a5279'); self.text(x1+37, y+18, '>', 13, CYAN, True); self.text(x1+55, y+18, line[:31], 9, WHITE, False, 'w')
        # Input panel
        self.box(left+16, h-215, w-25, h-45, '#071727', '#174365'); self.text(left+41, h-188, 'LATEST TRANSMISSION', 10, CYAN, True, 'w'); self.text(left+41, h-151, self.msg[:115], 12, WHITE, False, 'w')
        sx1, sx2 = w-150, w-25; self.button((sx1, h-104, sx2, h-58), 'EXECUTE', 'send'); self.box(480, h-104, sx1-14, h-58, '#071522', CYAN if self.hover == 'input' else '#1a5279')
        self.e.place(x=495, y=h-96, width=max(80, sx1-523), height=29)

    def tick(self):
        self.angle = (self.angle+(8 if self.listening else 2)) % 360; self.frame += 1; self.draw(); self.r.after(70 if self.listening else 500, self.tick)

    def action_at(self, x, y):
        w, h = self.r.winfo_width(), self.r.winfo_height(); right = 310 if self.logs_visible else 26; cx, cy = (294+w-right)/2, h*.39
        if w-275 < x < w-145 and 20 < y < 68: return 'logs'
        if w-130 < x < w-25 and 20 < y < 68: return 'exit'
        if 25 < x < 270 and 101 < y < 153: return 'commands'
        if (28 < x < 268 and h-218 < y < h-45) or (cx-160 < x < cx+160 and cy-160 < y < cy+160): return 'mic'
        if w-150 < x < w-25 and h-104 < y < h-58: return 'send'
        return ''

    def click(self, event): self.pressed = self.action_at(event.x, event.y); self.draw()
    def release(self):
        action = self.pressed; self.pressed = ''; self.draw()
        if action == 'logs': self.logs_visible = not self.logs_visible
        elif action == 'exit': self.close()
        elif action == 'commands': self.commands()
        elif action == 'mic': self.start()
        elif action == 'send': self.send()
    def set_hover(self, value):
        if self.hover != value: self.hover = value; self.r.configure(cursor='hand2' if value and value != 'input' else ''); self.draw()
    def motion(self, event): self.set_hover(self.action_at(event.x, event.y))

    def commands(self):
        dialog = tk.Toplevel(self.r); dialog.title('Jarvis Commands'); dialog.configure(bg=BG); dialog.geometry('560x420'); dialog.resizable(False, False)
        tk.Label(dialog, text='AVAILABLE COMMANDS', bg=BG, fg=CYAN, font=('Segoe UI', 20, 'bold')).pack(pady=(25, 16))
        for command in ['open google / youtube / chatgpt / instagram', 'play <song name>', 'who is <person> / what is <topic>', 'time / date / joke', 'exit / stop / bye']:
            tk.Label(dialog, text=command, bg=CARD, fg=WHITE, font=('Segoe UI', 11), anchor='w', padx=18, pady=10).pack(fill='x', padx=30, pady=4)

    def speaker(self):
        while True:
            phrase = self.q.get()
            if phrase is None: return
            self.engine.say(phrase); self.engine.runAndWait()
    def say(self, phrase):
        self.msg = phrase; self.logs.append('JARVIS: '+phrase); self.logs = self.logs[-20:]; self.q.put(phrase); self.draw()
    def send(self):
        phrase = self.e.get().strip(); self.e.delete(0, 'end')
        if phrase: self.run(phrase)
    def start(self):
        if self.listening: return
        self.listening = True; self.msg = 'Listening... please speak now.'; threading.Thread(target=self.hear, daemon=True).start()
    def hear(self):
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=.7); audio = recognizer.listen(source, timeout=6, phrase_time_limit=9)
            self.r.after(0, lambda: self.run(recognizer.recognize_google(audio)))
        except Exception: self.r.after(0, lambda: self.say('I could not hear you. Please try again.'))
        finally: self.r.after(0, lambda: setattr(self, 'listening', False))
    def run(self, phrase):
        self.listening = False; self.msg = 'You: '+phrase; self.logs.append('YOU: '+phrase); self.logs = self.logs[-20:]; self.draw(); threading.Thread(target=self.action, args=(phrase.lower(),), daemon=True).start()
    def action(self, phrase):
        try:
            sites = {'open google':'https://google.com', 'open youtube':'https://youtube.com', 'open chatgpt':'https://chatgpt.com', 'open instagram':'https://instagram.com'}
            if any(key in phrase for key in sites):
                key = next(key for key in sites if key in phrase); webbrowser.open(sites[key]); answer = 'Opening '+key[5:]
            elif phrase.startswith('play '): webbrowser.open('https://www.youtube.com/results?search_query='+quote_plus(phrase[5:])); answer = 'Opening YouTube results for '+phrase[5:]
            elif phrase.startswith(('who is ', 'what is ')): answer = wikipedia.summary(phrase.split(' is ', 1)[1], sentences=2)
            elif 'joke' in phrase: answer = pyjokes.get_joke()
            elif 'time' in phrase: answer = datetime.datetime.now().strftime('The time is %I:%M %p')
            elif 'date' in phrase: answer = datetime.datetime.now().strftime('Today is %d %B %Y')
            elif phrase in ('exit', 'stop', 'bye'): answer = 'Goodbye.'; self.r.after(1800, self.close)
            else: answer = 'I did not understand that. Select All Commands for help.'
            self.r.after(0, lambda: self.say(answer))
        except Exception: self.r.after(0, lambda: self.say('Sorry, that command failed.'))
    def close(self): self.q.put(None); self.r.destroy()


if __name__ == '__main__':
    root = tk.Tk(); Jarvis(root); root.mainloop()
