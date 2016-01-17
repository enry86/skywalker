#include <stdio.h>
#include <unistd.h>
#include <iostream>
#include <vector>
#include <opencv2/opencv.hpp>

#include "skywalker/image_shift.hpp"
#include "skywalker/sliding_average.hpp"

using namespace cv;

enum status {IDLE, TRACKING, CALIBRATION};

Mat getRotationMatrix(std::vector<double> shift, double center_x, double center_y) {
   Mat rot( 2, 3, CV_64FC1 );
   double sin = shift[1] / shift[2];
   double cos = shift[0] / shift[2];

   rot.at<double>(0,0) = cos;
   rot.at<double>(0,1) = sin;
   rot.at<double>(0,2) = (1-cos)*center_x - sin*center_y;
   rot.at<double>(1,0) = -1*sin;
   rot.at<double>(1,1) = cos;
   rot.at<double>(1,2) = sin*center_x + (1-cos)*center_y;

   return rot;
}


void capture_video (int dev, char *filename, bool test, int window) {
  VideoCapture *cap;
  status status = IDLE;
  Mat frame;
  Mat prev_frame;
  Mat rotation;
  ImageShift shift;
  SlidingAverage average(window);
  int key = 0;
  int frame_count = 0;
  bool stream_end = false;
  bool shift_init = false;
  bool calibration_completed = false;
  double curr_shift = 0.0;
  double prev_shift = 0.0;
  std::vector<double> shift_values;
  std::vector<double> shift_vec;
  
  if (test) {
    printf("Test mode: video file %s\n", filename);
    cap = new VideoCapture(filename);
  }
  else {
    printf("Live mode: device /dev/video%d\n", dev);
    cap = new VideoCapture(dev);
  }

  if (!cap->isOpened())
    throw "Empty stream";

  while (key != 27 && !stream_end) {
    *cap >> frame;
    frame_count++;
        
    if (frame.empty()) 
      stream_end = true;
    else {     

      if (key == 'c' && status == IDLE) {
	printf("Start Calibration\n");
	status = CALIBRATION;
	shift_init = false;	
	calibration_completed = false;
	frame_count = 0;
      }
      else if (status == CALIBRATION && frame_count == 250) {
	printf("Calibration completed\n");
	shift_init = false;
	status = IDLE;
	calibration_completed = true;	
	frame_count = 0;
	shift_values = shift.get_shift();
	printf ("Calibration results x,y,dist: %f, %f, %f\n",
		shift_values[0],
		shift_values[1],
		shift_values[2]);
	Point center(frame.cols >> 1, frame.rows >> 1);
	rotation = getRotationMatrix(shift_values, center.x, center.y);
      }
      else if (key == 32 && status == IDLE) {
	printf ("Tracking started\n");
	status = TRACKING;
	shift_init = false;
	
      }
      else if (key == 32 && status == TRACKING) {
	printf ("Tracking halted\n");
	status = IDLE;
	shift_init = false;
      }

      if (calibration_completed) {
	Mat rotated;
	warpAffine(frame, rotated, rotation, frame.size());
	rotated.copyTo(frame);
      }
      imshow("Frame", frame);	
      
      if (!shift_init) {
	shift.set_previous_frame(frame);
	shift_init = true;
      }
      shift.set_current_frame(frame);
      
      if (prev_frame.empty())
	frame.copyTo(prev_frame);
      

      if (status == TRACKING) {
	shift_vec = shift.get_shift();
	curr_shift = shift_vec[2];
	average.add_value(curr_shift - prev_shift);
	printf("%d, %f, %f, %f\n",
	       frame_count,
	       shift_vec[0],
	       shift_vec[1],
	       average.get_average());
	prev_shift = curr_shift;
      }

    }
    key = waitKey(5) & 0xff;
  }
  cap->release();
  delete cap;
}

void print_doc() {
  printf("Skywalker - Computer vision based telescope auto-guiding system\n");
  printf("\n");
  printf("Usage:\n");
  printf("\t-d <device nr>  : uses live feed from a v4l device /dev/videoX\n");
  printf("\t-f <video file> : test mode using a local video file\n");
  printf("\t-s <value>      : sliding average window size\n");
  printf("\t-h : prints this help\n");
  printf("\n");
  printf("If no argument are provided it starts acquiring live feed from /dev/video0\n");
  printf("\n");
  printf("May the force be with you\n");
  printf("\n");
}


int main(int argc, char **argv) {
  bool test = false, exit = false;
  int dev = 0;
  int window = 1;
  char *filename;
  int c;
  
  while ((c = getopt(argc, argv, "d:f:s:h")) != -1) {
    switch (c) {
    case 'd':
      test = false;
      dev = atoi(optarg);
      break;  
    case 'f':
      test = true;
      filename = optarg;
      break;
    case 's':
      window = atoi(optarg);
      break;
    case 'h':
      print_doc();
      exit = true;
      break;
    }    
  }

  if(!exit) {
    printf("Skywalker - Computer vision based telescope auto-guiding system\n");
    printf("\nPress [c] to start calibration\n");
    printf("Press [space] to start/halt tracking\n");
    printf("Press [esc] to quit\n");
    capture_video (dev, filename, test, window);
  }
  
  return 0;
}
