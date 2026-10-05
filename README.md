## Hardware
- Arduino Uno R3
- 16x2 LCD (HD44780) — displays the current problem
- Active/passive buzzer — chirps on a correct answer
- LED — flashes alongside the buzzer

## How it works
The Python script (`trainer_v2.py`) generates arithmetic problems matching
Zetamac's default difficulty (addition/subtraction 2-100, multiplication
2-12 x 2-100, division constructed to divide evenly) and runs a 120-second
timed session, identical to Zetamac's own format. Answers are typed into a
Tkinter window and checked live — no Enter key needed, matching Zetamac's
input behavior.

The Arduino (`mental_math_trainer_v2.ino`) is a pure output peripheral: it
receives the current problem over serial and displays it on the LCD, and
flashes the LED / sounds the buzzer when Python confirms a correct answer.

Each session is logged automatically (`mental_math_log.csv` for individual
problems, `sessions_log.csv` for session summaries), so scores are tracked
over time and directly comparable to Zetamac benchmark history.

## Why
Built as part of ongoing mental math training for quantitative trading
prep — speed and accuracy under time pressure, tracked longitudinally
rather than chasing one-off high scores.
