// -*- mode: c++ -*-
#ifndef PCM_H
#define PCM_H

#include <sndfile.h>
#include "sbsms.h"
#include "import.h"

class PcmReader : public AudioDecoder {
 public:
  PcmReader(const char *filename);
  ~PcmReader();
  long decode(audio_in_cb, long block_size, void *data);
  long read(float *buf, long block_size);
  int getChannels();
  int getSampleRate();
  long long int getFrames();
  bool isError();

 protected:
  bool bError;
  long total;
  SF_INFO info;
  SNDFILE *in;
};

class PcmWriter  {
 public:
  PcmWriter(const char *filename, sf_count_t samples, int samplerate, int chanels);
  ~PcmWriter();
  long write(float *buf, long block_size);
  void close();
  bool isError();

 protected:
  bool bError;
  long total;
  SF_INFO info;
  SNDFILE *out;

};

#endif
