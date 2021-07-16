// -*- mode: c++ -*-
#ifndef CONVERT_H
#define CONVERT_H

#include "sbsms.h"
#include "import.h"

using namespace _sbsms_;

typedef bool (*progress_cb)(float progress, const char *msg, void *data);

bool sbsms_convert(const char *filenameIn, const char *filenameOut, bool bAnalyze, bool bSynthesize, progress_cb progressCB, void *data, float stretch0 = 1.0f, float stretch1 = 1.0f, float pitch0 = 1.0f, float pitch1 = 1.0f, float volume = 1.0f);



class SBSMSInterfaceDecoderImp;
class SBSMSInterfaceDecoder : public SBSMSInterfaceSliding {
public:
  SBSMSInterfaceDecoder(Slide *rateSlide, Slide *pitchSlide, bool bPitchInputReference,
                        int channels, const SampleCountType &samples, long preSamples,
                        SBSMSQuality *quality, AudioDecoder *decoder, float pitch);
  virtual ~SBSMSInterfaceDecoder();
  long samples(audio *buf, long n);
  
protected:
  SBSMSInterfaceDecoderImp *imp;
};

#endif 
