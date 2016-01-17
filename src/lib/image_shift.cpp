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

std::vector<double> ImageShift::get_shift() {
  Mat curr_bw, curr_64, curr_gray;
  Mat prev_bw, prev_64, prev_gray;
  double amount = 0.0;
  std::vector<double> res(3);

  cvtColor(prev_frame, prev_gray, COLOR_BGR2GRAY);
  cvtColor(curr_frame, curr_gray, COLOR_BGR2GRAY);

  curr_bw = curr_gray > 120;
  prev_bw = prev_gray > 120;
  
  prev_bw.convertTo(prev_64, CV_64F);
  curr_bw.convertTo(curr_64, CV_64F);

  Point2d shift = phaseCorrelate(prev_64, curr_64);

  amount = std::sqrt(shift.x*shift.x + shift.y*shift.y);

  res[0] = shift.x;
  res[1] = shift.y;
  res[2] = amount;
  
  return res;
}

