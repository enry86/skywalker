#include <stdio.h>
#include <unistd.h>
#include <opencv2/opencv.hpp>

#include "skywalker/image_shift.hpp"

using namespace cv;

void capture_video (int dev, char *filename, bool test) {
  VideoCapture *cap;  
  Mat frame, prev_frame;
  int key = 0;
  bool stream_end = false, shift_total_init = false;
  ImageShift shift, shift_total;

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
    if (!shift_total_init) {
      shift_total.set_previous_frame(frame);
      shift_total_init = true;
    }
    else
      shift_total.set_current_frame(frame);
    
    if (frame.empty()) 
      stream_end = true;
    else {
      imshow("Frame", frame);
      frame.copyTo(prev_frame);

      shift.set_current_frame(frame);
      
      printf("Amount of shift between consecutive frames: %f\n",
	     shift.get_shift());
      printf("Amount of shift between first and last frames: %f\n",
	     shift_total.get_shift());
      
      shift.set_previous_frame(prev_frame);    
    }
    key = waitKey() & 0xff;
  }
  cap->release();
  delete cap;
}



int main(int argc, char **argv) {
  bool test = false;
  int dev = 0;
  char *filename;
  int c;
  
  while ((c = getopt(argc, argv, "d:f:")) != -1) {
    switch (c) {
    case 'd':
      test = false;
      dev = atoi(optarg);
      break;  
    case 'f':
      test = true;
      filename = optarg;
      break;
    }
  }

  capture_video (dev, filename, test);
  
  return 0;
}
