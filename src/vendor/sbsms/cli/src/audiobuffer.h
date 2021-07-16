// -*- mode: c++ -*-
#ifndef RINGBUFFER_H
#define RINGBUFFER_H

#include <pthread.h>

class AudioBuffer {

 public:
  AudioBuffer(long size, int channels);
  ~AudioBuffer();

  long read(float *outputBuffer, long block_size);
  long write(float *buf, long n);
  void writingComplete();
  void readingComplete();
  long getSamplesQueued();
  void flush();
  bool isFull();

 protected:
  bool isWriteReady();
  bool isReadReady();
  void copy(float *out, long outOffset, float *in, long inOffset, long n);
  pthread_cond_t importWriteCondition;
  pthread_mutex_t importWriteMutex;
  pthread_cond_t importReadCondition;
  pthread_mutex_t importReadMutex;
  pthread_mutex_t importMutex;

  bool bReadFlush;
  int channels;
  float *shareBuf;
  long readBlockSize;
  long shareBufStart;
  long shareBufEnd;
  long shareBufSize;
  long halfShareBufSize;
};

#endif
