//this class evaluates the amount of shift between two images
#include <opencv2/opencv.hpp>

class ImageShift {
  cv::Mat curr_frame;
  cv::Mat prev_frame;

public:
  ImageShift ();
  ImageShift (cv::Mat, cv::Mat);
  void set_previous_frame (cv::Mat);
  void set_current_frame (cv::Mat);
  double get_shift();
};
