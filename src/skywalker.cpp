#include <stdio.h>
#include <unistd.h>
#include <chrono>
#include <ctime>
#include <iostream>
#include <opencv2/opencv.hpp>

#include "skywalker/image_shift.hpp"

using namespace cv;

void capture_video (int dev, char *filename, bool test) {
  std::chrono::time_point<std::chrono::system_clock> start, end;
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
    start = std::chrono::system_clock::now();
    *cap >> frame;
    if (!shift_total_init) {
      shift_total.set_previous_frame(frame);
      shift_total_init = true;
    }
    shift_total.set_current_frame(frame);
    
    if (frame.empty()) 
      stream_end = true;
    else {
      imshow("Frame", frame);
      if (prev_frame.empty())
	frame.copyTo(prev_frame);
      
      shift.set_previous_frame(prev_frame);    
      shift.set_current_frame(frame);

      frame.copyTo(prev_frame);

      end = std::chrono::system_clock::now();
      
      printf("Amount of shift between consecutive frames: %f\n",
	     shift.get_shift());
      printf("Amount of shift between first and last frames: %f\n",
	     shift_total.get_shift());
      std::chrono::duration<double> elapsed_seconds = end-start;
      std::time_t end_time = std::chrono::system_clock::to_time_t(end);
      
      std::cout << "elapsed time: " << elapsed_seconds.count() << "s\n";
      
    }
    key = waitKey() & 0xff;
  }
  cap->release();
  delete cap;
}

void print_doc() {
  printf("Skywalker - Computer vision based telescope auto-guiding system\n");
  printf("\n");
  printf("Usage:\n");
  printf("\t-d <device nr> : uses live feed from a v4l device /dev/videoX\n");
  printf("\t-f <video file> : test mode using a local video file\n");
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
  char *filename;
  int c;
  
  while ((c = getopt(argc, argv, "d:f:h")) != -1) {
    switch (c) {
    case 'd':
      test = false;
      dev = atoi(optarg);
      break;  
    case 'f':
      test = true;
      filename = optarg;
      break;
    case 'h':
      print_doc();
      exit = true;
      break;
    }    
  }

  if(!exit)
    capture_video (dev, filename, test);
  
  return 0;
}
