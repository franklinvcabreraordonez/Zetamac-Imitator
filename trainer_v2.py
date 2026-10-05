

import serial
import time
import random
import csv
import os
import tkinter as tk
from datetime import datetime
from collections import defaultdict

SERIAL_PORT = 'COM3'
BAUD = 9600
LOG_FILE = 'mental_math_log.csv'
SESSION_LOG_FILE = 'sessions_log.csv'
DAILY_SUMMARY_FILE = 'daily_summary.csv'
TIME_LIMIT_SEC = 120

OPS = ['+', '-', '*', '/']

#Color coded results so progress can be tracked 
SCORE_BANDS = [
    (0,   "#e8eef5"),   
    (50,  "#d3e4f5"),   
    (60,  "#cdeedd"),   
    (70,  "#fff3b0"),   
    (80,  "#ffd9a0"),   
    (90,  "#ffb3b3"),   
    (100, "#f5a3d9"),   
]


def get_score_color(score):
    color = SCORE_BANDS[0][1]
    for threshold, c in SCORE_BANDS:
        if score >= threshold:
            color = c
        else:
            break
    return color


def generate_problem():
    op = random.choice(OPS)
    if op == '+':
        a, b = random.randint(2, 100), random.randint(2, 100)
        answer = a + b
    elif op == '-':
        a, b = random.randint(2, 100), random.randint(2, 100)
        if b > a:
            a, b = b, a
        answer = a - b
    elif op == '*':
        a, b = random.randint(2, 12), random.randint(2, 100)
        answer = a * b
    else:
        b = random.randint(2, 12)
        answer = random.randint(2, 100)
        a = b * answer
    return op, a, b, answer


def log_row(row):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'op', 'a', 'b', 'answer', 'response_ms'])
        writer.writerow(row)


def log_session(score, total):
    file_exists = os.path.isfile(SESSION_LOG_FILE)
    with open(SESSION_LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'score', 'total_attempted', 'accuracy'])
        accuracy = score / total if total > 0 else 0
        writer.writerow([datetime.now().isoformat(), score, total, f"{accuracy:.3f}"])


def recompute_daily_summary():
    if not os.path.isfile(SESSION_LOG_FILE):
        return None

    by_date = defaultdict(list)
    with open(SESSION_LOG_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = datetime.fromisoformat(row['timestamp']).date().isoformat()
            by_date[d].append(int(row['score']))

    with open(DAILY_SUMMARY_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'runs', 'high_score', 'low_score', 'avg_score'])
        for d in sorted(by_date):
            scores = by_date[d]
            writer.writerow([d, len(scores), max(scores), min(scores),
                              f"{sum(scores) / len(scores):.1f}"])

    today = datetime.now().date().isoformat()
    if today in by_date:
        scores = by_date[today]
        return {'runs': len(scores), 'high': max(scores),
                'low': min(scores), 'avg': sum(scores) / len(scores)}
    return None


class TrainerApp:
    def __init__(self, root, ser):
        self.root = root
        self.ser = ser
        self.score = 0
        self.total = 0
        self.session_start = time.time()
        self.question_start = None
        self.current = None
        self.ended = False

        root.title("Mental Math Trainer")
        root.configure(bg="white")
        root.geometry("500x340")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.timer_label = tk.Label(root, text="", font=("Helvetica", 16), bg="white", fg="#555")
        self.timer_label.pack(pady=(20, 0))

        self.score_label = tk.Label(root, text="Score: 0", font=("Helvetica", 16, "bold"),
                                     bg=get_score_color(0), fg="#333", width=20, pady=6)
        self.score_label.pack(pady=(5, 0))

        self.problem_label = tk.Label(root, text="", font=("Helvetica", 40), bg="white", fg="black")
        self.problem_label.pack(pady=30)

        self.var = tk.StringVar()
        self.var.trace_add("write", self.on_type)
        self.entry = tk.Entry(root, font=("Helvetica", 24), justify="center", width=8,
                               textvariable=self.var)
        self.entry.pack()
        self.entry.focus()

        self.daily_label = tk.Label(root, text="", font=("Helvetica", 13), bg="white", fg="#777")
        self.daily_label.pack(pady=(15, 0))

        self.next_problem()
        self.update_timer()

    def next_problem(self):
        op, a, b, answer = generate_problem()
        self.current = (op, a, b, answer)
        self.problem_label.config(text=f"{a} {op} {b} =")
        self.question_start = time.time()
        self.ser.write(f"Q,{op},{a},{b}\n".encode())
        self.var.set("")

    def on_type(self, *args):
        if self.ended:
            return
        raw = self.var.get()
        op, a, b, answer = self.current
        if raw == str(answer):
            response_ms = int((time.time() - self.question_start) * 1000)
            self.total += 1
            self.score += 1

            log_row([datetime.now().isoformat(), op, a, b, answer, response_ms])
            self.ser.write("R,1\n".encode())

            self.score_label.config(text=f"Score: {self.score}",
                                     bg=get_score_color(self.score))
            self.next_problem()

    def update_timer(self):
        if self.ended:
            return
        elapsed = time.time() - self.session_start
        remaining = max(0, TIME_LIMIT_SEC - elapsed)
        self.timer_label.config(text=f"{remaining:.0f}s")

        if remaining <= 0:
            self.end_session()
        else:
            self.root.after(200, self.update_timer)

    def end_session(self):
        self.ended = True
        self.entry.config(state="disabled")
        self.problem_label.config(text="Time's up!", font=("Helvetica", 32))
        self.timer_label.config(text=f"Final score: {self.score} / {self.total}")
        self.score_label.config(bg=get_score_color(self.score))
        log_session(self.score, self.total)

        stats = recompute_daily_summary()
        if stats:
            self.daily_label.config(
                text=f"Today ({stats['runs']} runs): high {stats['high']}, "
                     f"low {stats['low']}, avg {stats['avg']:.1f}")

        self.ser.write(f"D,{self.score},{self.total}\n".encode())

    def on_close(self):
        if not self.ended:
            log_session(self.score, self.total)
            recompute_daily_summary()
        self.root.destroy()


def main():
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
    time.sleep(2)
    root = tk.Tk()
    TrainerApp(root, ser)
    root.mainloop()
    ser.close()


if __name__ == '__main__':
    main()