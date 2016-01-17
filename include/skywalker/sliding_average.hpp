//This class implements a sliding window average, used to smooth shift values
#include <queue>

class SlidingAverage {
  std::queue<double> buffer;
  double running_sum = 0.0;
  int window_size = 1;

public:
  SlidingAverage(int);
  void add_value(double);
  double get_average();
  void reset();
  void reset(int);
};
