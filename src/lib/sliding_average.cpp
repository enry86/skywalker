#include "skywalker/sliding_average.hpp"
#include <unistd.h>
#include <iostream>

SlidingAverage::SlidingAverage(int size) {
  window_size = size;
}

void SlidingAverage::reset(int size) {
  reset();
  window_size = size;
}

void SlidingAverage::reset() {
  running_sum = 0.0;
  while (!buffer.empty())
    buffer.pop();
}

void SlidingAverage::add_value (double val)  {
  buffer.push(val);
  running_sum += val;
  
  if (buffer.size() > window_size) {
    running_sum -= buffer.front();
    buffer.pop();
  }
}

double SlidingAverage::get_average () {
  if (buffer.size() == 0)
    return 0.0;
  else
    return running_sum / buffer.size();
}
