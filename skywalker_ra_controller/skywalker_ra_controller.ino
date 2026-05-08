/*
  SkyWalker RA controller (phase 2)
  ---------------------------------
  Serial protocol:
    - SET <speed>\n   : set signed speed command from Python
    - STOP\n          : immediate stop
    - PING\n          : replies PONG
    - STATUS\n        : prints current state

  This sketch maps signed speed commands to Adafruit Motor Shield v1
  commands through AFMotor.h (DC motor channel M1..M4).
*/

#include <AFMotor.h>

// -------------------- User-tunable hardware config --------------------
// Choose motor channel and PWM frequency for your wiring.
// Channel: 1..4 maps to M1..M4 outputs on the shield.
static const uint8_t MOTOR_CHANNEL = 4;
static const uint8_t MOTOR_FREQUENCY = MOTOR12_1KHZ;

static const bool DIR_INVERTED = false;

// ---------------------- Control and safety config ----------------------
static const long SERIAL_BAUD = 115200;
static const unsigned long WATCHDOG_TIMEOUT_MS = 12000;

// Input speed (from Python SET command) is mapped to PWM via SPEED_TO_PWM.
// Example: speed=1.2 and SPEED_TO_PWM=120 => pwm=144.
static const float SPEED_TO_PWM = 120.0f;
static const int PWM_MAX = 255;
static const int PWM_MIN_EFFECTIVE = 0;

// ----------------------------------------------------------------------

float targetSpeed = 0.0f;
unsigned long lastCommandMs = 0;
AF_DCMotor motor(MOTOR_CHANNEL, MOTOR_FREQUENCY);

void setup() {
  Serial.begin(SERIAL_BAUD);

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
    Serial.print(speedToPwm(targetSpeed));
    Serial.print(" channel=M");
    Serial.println(MOTOR_CHANNEL);
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
  motor.setSpeed((uint8_t)pwm);

  if (pwm == 0) {
    motor.run(RELEASE);
    return;
  }

  bool forward = speed >= 0.0f;
  if (DIR_INVERTED) {
    forward = !forward;
  }
  motor.run(forward ? FORWARD : BACKWARD);
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
