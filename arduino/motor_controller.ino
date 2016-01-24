#include <AFMotor.h>

AF_DCMotor motor(1);

int current_speed = 0;
int serial_data = 0;

void setup() {
  Serial.begin(9600);
  motor.setSpeed(current_speed);
  motor.run(FORWARD);
}

void loop() {
  if(Serial.available() > 0) {
    serial_data = Serial.read();
    current_speed = serial_data;
    motor.setSpeed(current_speed);
    Serial.print("current_speed ");
    Serial.println(serial_data, DEC);
  }
  
}

