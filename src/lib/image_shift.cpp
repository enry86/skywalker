//this class evaluates the amount of shift between two images
#include "skywalker/image_shift.hpp"

using namespace cv;

ImageShift::ImageShift () {}

ImageShift::ImageShift (Mat prev, Mat curr) {
  prev.copyTo(prev_frame);
  curr.copyTo(curr_frame);
}

void ImageShift::set_previous_frame (Mat prev) {
  prev.copyTo(prev_frame);
}

void ImageShift::set_current_frame (Mat curr) {
  curr.copyTo(curr_frame);
}

double ImageShift::get_shift() {
  return 0.0;
}

