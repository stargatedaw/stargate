//#include "config.h"

#include "convert.h"
#include "pcm.h"
#include "real.h"
#include <stdlib.h>
#include <algorithm>
#include "import.h"
#include <cstring>

using namespace std;
using namespace _sbsms_;

long copy_audio_buf(audio *to, long off1, audio *from, long off2, long n)
{
  memcpy(to+off1,from+off2,n*sizeof(audio));
  return n;
}

long audio_convert_from(float *to, long off1, audio *from, long off2, long n, int channels)
{
  int n2 = n+off2;
  if(channels == 2) {
    int k1 = off1<<1;
    for(int k=off2;k<n2;k++) {
      to[k1++] = (float)from[k][0];
      to[k1++] = (float)from[k][1];
    }
  } else {
    int k1 = off1;
    for(int k=off2;k<n2;k++) {
      to[k1++] = (float)from[k][0];
    }
  }
  return n;
}

long audio_convert_to(audio *to, long off1, float *from, long off2, long n, int channels)
{
  int n1 = n + off1;
  if(channels == 2) {
    int k2 = off2<<1;
    for(int k=off1;k<n1;k++) {
      to[k][0] = (float)from[k2++];
      to[k][1] = (float)from[k2++];
    }
  } else {
    int k2 = off2;
    for(int k=off1;k<n1;k++) {
      to[k][0] = (float)from[k2];
      to[k][1] = (float)from[k2++];
    }
  }
  return n;
}



class SBSMSInterfaceDecoderImp {
public:
  SBSMSInterfaceDecoderImp(int channels,SBSMSQuality *quality, AudioDecoder *decoder, float pitch);

  virtual ~SBSMSInterfaceDecoderImp();
  inline long samples(audio *buf, long n);
  
  Resampler *preResampler;
  int channels;
  float *buf;
  audio *abuf;
  float pitch;
  SampleCountType samplesIn;
  long block;
  AudioDecoder *decoder;
};

long convertResampleCB(void *cb_data, SBSMSFrame *data) 
{
  SBSMSInterfaceDecoderImp *iface = (SBSMSInterfaceDecoderImp*) cb_data;
  long n_read_in = iface->decoder->read(iface->buf,iface->block);
  audio_convert_to(iface->abuf,0,iface->buf,0,n_read_in,iface->channels);
  iface->samplesIn += n_read_in;
  data->size = n_read_in;
  data->ratio0 = iface->pitch;
  data->ratio1 = iface->pitch;
  data->buf = iface->abuf;
  return n_read_in;
}

SBSMSInterfaceDecoderImp :: SBSMSInterfaceDecoderImp(int channels, SBSMSQuality *quality, AudioDecoder *decoder, float pitch)
{
  this->preResampler = new Resampler(convertResampleCB, this, pitch==1.0f?SlideIdentity:SlideConstant);
  this->channels = channels;
  this->block = quality->getFrameSize();
  this->decoder = decoder;
  this->pitch = pitch;
  samplesIn = 0;
  buf = (float*)calloc(block*channels,sizeof(float));
  abuf = (audio*)calloc(block,sizeof(audio));
}

SBSMSInterfaceDecoderImp :: ~SBSMSInterfaceDecoderImp()
{
  free(buf);
  free(abuf);
  delete preResampler;
}
  
long SBSMSInterfaceDecoderImp :: samples(audio *buf, long n)
{ 
  return preResampler->read(buf, n);
}
  
SBSMSInterfaceDecoder :: SBSMSInterfaceDecoder(Slide *rateSlide, Slide *pitchSlide, bool bPitchInputReference,
                                               int channels, const SampleCountType &samples, long preSamples,
                                               SBSMSQuality *quality, AudioDecoder *decoder, float pitch) 
  : SBSMSInterfaceSliding(rateSlide,pitchSlide,bPitchInputReference,samples,preSamples,quality) 
{
  imp = new SBSMSInterfaceDecoderImp(channels,quality,decoder,pitch);
}

SBSMSInterfaceDecoder :: ~SBSMSInterfaceDecoder()
{
  delete imp;
}

long SBSMSInterfaceDecoder :: samples(audio *buf, long n)
{
  return imp->samples(buf,n);
}

bool sbsms_convert(const char *filenameIn, const char *filenameOut, bool bAnalyze, bool bSynthesize, progress_cb progressCB, void *data, float rate0, float rate1, float pitch0, float pitch1, float volume)
{  
  bool status = true;
  int srOut = 44100;
  long blockSize;
  int channels;
  SampleCountType samplesIn;
  int srIn;
  SampleCountType samplesToOutput;
  SampleCountType samplesToInput;
  bool bRead = false;
  bool bWrite = false;
  audio *abuf = NULL;
  float *fbuf = NULL;
  SBSMSInterface *iface = NULL;
  SBSMSInterface *ifacePre = NULL;
  SBSMS *sbsms = NULL;
  PcmWriter *writer = NULL;
  AudioDecoder *decoder = NULL;
  AudioDecoder *decoderPre = NULL;

  SBSMSQuality quality(&SBSMSQualityStandard);
  Slide rateSlide(SlideLinearInputRate,rate0,rate1);
  Slide pitchSlide(SlideLinearOutputRate,pitch0,pitch1);

  if(bAnalyze) {
    float preProgress = 0.0f;
    decoder = import(filenameIn);
    if(!decoder) {
      printf("File: %s cannot be opened\n",filenameIn);
      exit(-1);
    }
    srIn = decoder->getSampleRate();
    channels = decoder->getChannels();
    samplesIn = decoder->getFrames();
    samplesToInput = (SampleCountType) (samplesIn*(float)srOut/(float)srIn);
    float pitch = (srOut == srIn?1.0f:(float)srOut / (float)srIn);
    iface = new SBSMSInterfaceDecoder(&rateSlide,&pitchSlide,false,
                                      channels,samplesToInput,0,&quality,decoder,pitch);
    sbsms = new SBSMS(channels,&quality,bSynthesize);

    samplesToOutput = iface->getSamplesToOutput();
 
    if(bSynthesize) {
      blockSize = quality.getFrameSize();
      fbuf = (float*)calloc(blockSize*channels,sizeof(float));
      abuf = (audio*)calloc(blockSize,sizeof(audio));    
      writer = new PcmWriter(filenameOut,samplesToOutput,srOut,channels);
      if(writer->isError()) {
        printf("File: %s cannot be opened\n",filenameOut);
        status = false;
        goto cleanup;
      }

      SampleCountType pos = 0;
      long ret = -1;
      
      while(pos<samplesToOutput && ret) {
        long lastPercent=0;      
        ret = sbsms->read(iface,abuf,blockSize);
        if(pos+ret > samplesToOutput) {
          ret = (long)(samplesToOutput - pos);
        }
        audio_convert_from(fbuf,0,abuf,0,ret,channels);
        for(int k=0;k<ret*channels;k++) {
          fbuf[k] *= volume;
        }
      
        if(ret) writer->write(fbuf, ret);
        pos += ret;
        
        float progress = (float)pos / (float)samplesToOutput;
        progressCB(progress,"Progress",data);
      }
      writer->close();
    }
  }
  
 cleanup:
  if(decoderPre) delete decoderPre;
  if(decoder) delete decoder;
  if(fbuf) free(fbuf);
  if(abuf) free(abuf);
  if(sbsms) delete sbsms;
  if(iface) delete iface;
  if(ifacePre) delete ifacePre;
  if(writer) delete writer;

  return status;
}
