#include "skywalker/arduino_serial.hpp"
#include <fstream>

ArduinoSerial::ArduinoSerial(char *device) {
  arduino.open(device, std::ios::binary | std::ios::out); 
}

ArduinoSerial::~ArduinoSerial() {
  arduino.close();
}

int ArduinoSerial::setSpeed(unsigned char value) {
  int res = value;
  if (value >= 0 && value <= 255) {
    arduino.write((char *)&value, sizeof(value));
    arduino.flush();
  }
  else
    res = -1;
  return res;
}
