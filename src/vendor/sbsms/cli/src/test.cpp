#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "convert.h"

bool progressCB(float progress, const char *msg, void *data) {
  static int lastPercent = 0;
  int percent = (int)(100.0f * progress);
  if(lastPercent != percent) {
    //printf("\r%s: %3i%% [%-40s] ", msg, percent>100?100:percent, &"||||||||||||||||||||||||||||||||||||||||"[40 - ((percent>100)?40:(2*percent/5))] );
    lastPercent = percent;
    fflush(stdout);
  }
  return true;
}

int main(int argc, char **argv)
{
#ifdef _WIN32
	int status = pthread_win32_process_attach_np();
#endif

  if(argc<7) {
    printf("usage: sbsms infile<.wav|.aif|.mp3|.sbsms> outfile<.wav|.aif|.sbsms> rate-start[0.01:100] rate-end[0.01:100] halfsteps-start[-48:48] halfsteps-end[-48:48]\n");
    exit(-1);
  }

  bool bAnalyze;
  bool bSynthesize;
  char *filenameIn = argv[1];
  char *filenameOut = argv[2];
  
  if(strstr(filenameIn,".sbsms")) {
    bAnalyze = false;
  } else {
    bAnalyze = true;
  }
  if(strstr(filenameOut,".sbsms")) {
    bSynthesize = false;
  } else {
    bSynthesize = true;
  }
  if(!bAnalyze && !bSynthesize) {
    printf("Can't convert from .sbsms to .sbsms format\n");
    exit(-1);
  }
  
  float rate0 = (float)atof(argv[3]);
  float rate1 = (float)atof(argv[4]);
  float halfsteps0 = (float)atof(argv[5]);
  float halfsteps1 = (float)atof(argv[6]);
  if(rate0 < 0.01f || rate0 > 100.0f) {
    printf("rate-start out of bounds\n");
    exit(-1);
  }
  if(rate1 < 0.01f || rate1 > 100.0f) {
    printf("rate-end out of bounds\n");
    exit(-1);
  }
  if(halfsteps0 < -48.0f || halfsteps0 > 48.0f) {
    printf("halfsteps-start out of bounds\n");
    exit(-1);
  }
  if(halfsteps1 < -48.0f || halfsteps1 > 48.0f) {
    printf("halfsteps-end out of bounds\n");
    exit(-1);
  }
    
  float pitch0 = pow(2.0f,halfsteps0/12.0f);
  float pitch1 = pow(2.0f,halfsteps1/12.0f);
  
  while(1) {
    sbsms_convert(filenameIn, filenameOut, bAnalyze, bSynthesize, progressCB, NULL, rate0, rate1, pitch0, pitch1, 1.0f);
    break;
  }
  printf("\n");
}
