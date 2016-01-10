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
  Mat curr_bw, curr_64, curr_gray;
  Mat prev_bw, prev_64, prev_gray;
  double amount = 1.0;

  cvtColor(prev_frame, prev_gray, COLOR_BGR2GRAY);
  cvtColor(curr_frame, curr_gray, COLOR_BGR2GRAY);

  curr_bw = curr_gray > 100;
  prev_bw = prev_gray > 100;
  
  prev_bw.convertTo(prev_64, CV_64F);
  curr_bw.convertTo(curr_64, CV_64F);


  
  Point2d shift = phaseCorrelate(prev_64, curr_64);

  /*
  Point center(curr_frame.cols >> 1, curr_frame.rows >> 1);
  circle(curr_frame, center, (int)amount, Scalar(0, 255, 0), 3, LINE_AA);
  line(curr_frame, center, Point(center.x + (int)shift.x, center.y + (int)shift.y), Scalar(0, 255, 0), 3, LINE_AA);
  circle(curr_frame,Point(center.x + (int)shift.x, center.y + (int)shift.y), (int)amount, Scalar(0, 0, 255), 3, LINE_AA);
  
  imshow("TEST", curr_frame);
  
  printf("SHIFT: %f, %f\n", shift.x, shift.y);
  */

  amount = std::sqrt(shift.x*shift.x + shift.y*shift.y);
  
  return amount;
}

