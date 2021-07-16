#include <stdlib.h>
#include <stdio.h>

#include "pcm.h"
#include <algorithm>
using namespace std;

long PcmReader :: read(float *buf, long block_size) {
  long nread = (long)sf_readf_float(in, buf, block_size);
  return nread;
}

PcmReader :: PcmReader(const char *filename) 
{
  total = 0;
  in = sf_open(filename, SFM_READ, &info);
  
  bError = false;
  if (!in) {
    perror("cannot open file for reading");
    bError = true;
  }
}

bool PcmReader :: isError()
{
  return bError;
}

int PcmReader :: getSampleRate()
{
  return info.samplerate;
}

long long int PcmReader :: getFrames()
{
  return (long long int)info.frames;
}

int PcmReader :: getChannels()
{
  return info.channels;
}

PcmReader :: ~PcmReader() 
{  
  sf_close(in);
}

PcmWriter :: PcmWriter(const char *filename, sf_count_t size, int samplerate, int channels) 
{
  total = 0;
  info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
  info.frames = size;
  info.samplerate = samplerate;
  info.channels = channels;
  info.sections = 1;
  info.seekable = 0;

  if (!sf_format_check(&info))
    info.format = (info.format & SF_FORMAT_TYPEMASK);

  out = sf_open(filename, SFM_WRITE, &info);

  bError = false;
  if (!sf_format_check(&info)) {
    bError = true;
    perror("bad format for writing pcm");
  }
  if (!out) {
    perror("cannot open file for writing");
    bError = true;
  }
}

bool PcmWriter :: isError()
{
  return bError;
}

long PcmWriter :: write(float *data, long n)
{
  return (long)sf_writef_float(out, (float *)data, n);
}
 
PcmWriter :: ~PcmWriter()
{
}

void PcmWriter :: close() 
{
  if(out) sf_close(out);
}
