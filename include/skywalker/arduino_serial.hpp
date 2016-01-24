#include <fstream>

class ArduinoSerial {
  std::ofstream arduino;

public:
  ArduinoSerial(char *device);
  ~ArduinoSerial();
  int setSpeed(unsigned char value);

};
