/*
  SkyWalker RA controller (phase 2)
  ---------------------------------
  Serial protocol:
    - SET <speed>\n   : set signed speed command from Python
    - STOP\n          : immediate stop
    - PING\n          : replies PONG
    - STATUS\n        : prints current state

  This sketch maps signed speed commands to DIR + PWM outputs for a
  motor driver shield/H-bridge. Adapt pin numbers and polarity below.
*/

// -------------------- User-tunable hardware config --------------------
static const int DIR_PIN = 7;
static const int PWM_PIN = 9;
static const int ENABLE_PIN = 8;  // Set to -1 if your driver has no enable pin

static const bool DIR_INVERTED = false;
static const bool ENABLE_ACTIVE_HIGH = true;

// ---------------------- Control and safety config ----------------------
static const long SERIAL_BAUD = 115200;
static const unsigned long WATCHDOG_TIMEOUT_MS = 1200;

// Input speed (from Python SET command) is mapped to PWM via SPEED_TO_PWM.
// Example: speed=1.2 and SPEED_TO_PWM=120 => pwm=144.
static const float SPEED_TO_PWM = 120.0f;
static const int PWM_MAX = 255;
static const int PWM_MIN_EFFECTIVE = 0;

// ----------------------------------------------------------------------

float targetSpeed = 0.0f;
unsigned long lastCommandMs = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);

  pinMode(DIR_PIN, OUTPUT);
  pinMode(PWM_PIN, OUTPUT);
  if (ENABLE_PIN >= 0) {
    pinMode(ENABLE_PIN, OUTPUT);
    setDriverEnabled(true);
  }

  applyMotorCommand(0.0f);
  lastCommandMs = millis();
  Serial.println("READY");
}

void loop() {
  handleSerialLines();
  watchdogCheck();
}

void handleSerialLines() {
  while (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) {
      continue;
    }
    processCommand(line);
  }
}

void processCommand(const String &line) {
  if (line.startsWith("SET ")) {
    String payload = line.substring(4);
    float speed = payload.toFloat();
    targetSpeed = speed;
    applyMotorCommand(targetSpeed);
    lastCommandMs = millis();

    Serial.print("ACK ");
    Serial.println(targetSpeed, 6);
    return;
  }

  if (line == "STOP") {
    targetSpeed = 0.0f;
    applyMotorCommand(0.0f);
    lastCommandMs = millis();
    Serial.println("ACK STOP");
    return;
  }

  if (line == "PING") {
    Serial.println("PONG");
    return;
  }

  if (line == "STATUS") {
    Serial.print("STATUS speed=");
    Serial.print(targetSpeed, 6);
    Serial.print(" pwm=");
    Serial.println(speedToPwm(targetSpeed));
    return;
  }

  Serial.print("ERR unknown: ");
  Serial.println(line);
}

void watchdogCheck() {
  unsigned long now = millis();
  if (now - lastCommandMs > WATCHDOG_TIMEOUT_MS) {
    if (targetSpeed != 0.0f) {
      targetSpeed = 0.0f;
      applyMotorCommand(0.0f);
      Serial.println("WATCHDOG STOP");
    }
  }
}

void applyMotorCommand(float speed) {
  int pwm = speedToPwm(speed);
  bool forward = speed >= 0.0f;
  if (DIR_INVERTED) {
    forward = !forward;
  }

  digitalWrite(DIR_PIN, forward ? HIGH : LOW);
  analogWrite(PWM_PIN, pwm);
}

int speedToPwm(float speed) {
  float mapped = abs(speed) * SPEED_TO_PWM;
  if (mapped > PWM_MAX) {
    mapped = PWM_MAX;
  }
  int pwm = (int)(mapped + 0.5f);
  if (pwm > 0 && pwm < PWM_MIN_EFFECTIVE) {
    pwm = PWM_MIN_EFFECTIVE;
  }
  return pwm;
}

void setDriverEnabled(bool enabled) {
  if (ENABLE_PIN < 0) {
    return;
  }
  bool level = ENABLE_ACTIVE_HIGH ? enabled : !enabled;
  digitalWrite(ENABLE_PIN, level ? HIGH : LOW);
}
