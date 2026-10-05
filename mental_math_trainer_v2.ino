#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int BUZZER_PIN = 10;
const int LED_PIN = 8;

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  lcd.print("Mental Math");
  lcd.setCursor(0, 1);
  lcd.print("Trainer v2");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("Q,")) {
      displayProblem(line);
    } else if (line.startsWith("R,")) {
      handleFeedback(line);
    } else if (line.startsWith("D,")) {
      displayFinalScore(line);
    }
  }
}

void displayProblem(String line) {
  int idx1 = line.indexOf(',', 2);
  int idx2 = line.indexOf(',', idx1 + 1);

  String op = line.substring(2, idx1);
  String a = line.substring(idx1 + 1, idx2);
  String b = line.substring(idx2 + 1);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(a + " " + op + " " + b + " =");
  lcd.setCursor(0, 1);
  lcd.print("(type in PC)");
}

void handleFeedback(String line) {
  int correct = line.substring(2).toInt();

  if (correct == 1) {
    digitalWrite(LED_PIN, HIGH);
    chirp();
    digitalWrite(LED_PIN, LOW);
  }
}

void displayFinalScore(String line) {
  int idx1 = line.indexOf(',', 2);
  String score = line.substring(2, idx1);
  String total = line.substring(idx1 + 1);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Time's up!");
  lcd.setCursor(0, 1);
  lcd.print("Score: " + score + "/" + total);
}

void chirp() {
  for (int v = 0; v <= 180; v += 30) {
    analogWrite(BUZZER_PIN, v);
    delay(3);
  }
  delay(80);
  for (int v = 180; v >= 0; v -= 30) {
    analogWrite(BUZZER_PIN, v);
    delay(3);
  }
  analogWrite(BUZZER_PIN, 0);
}