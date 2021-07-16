#include "audiobuffer.h"
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <algorithm>
#include <assert.h>
using namespace std;

void AudioBuffer :: copy(float *out, long outOffset, float *in, long inOffset, long n)
{
  if(channels==1)
    memcpy(out+outOffset,in+inOffset,n*sizeof(float));
  else if(channels==2)
    memcpy(out+(outOffset<<1),in+(inOffset<<1),(n<<1)*sizeof(float));
}

AudioBuffer :: AudioBuffer(long size, int channels)
{
  pthread_cond_init(&importWriteCondition, NULL);
  pthread_mutex_init(&importWriteMutex, NULL);
  pthread_cond_init(&importReadCondition, NULL);
  pthread_mutex_init(&importReadMutex, NULL);
  pthread_mutex_init(&importMutex, NULL);
  
  shareBufStart = 0;
  shareBufEnd = 0;
  readBlockSize = 0;
  bReadFlush = false;
  this->channels = channels;
  shareBuf = new float[channels*size];
  shareBufSize = size;
  halfShareBufSize = size/2;
}

AudioBuffer :: ~AudioBuffer()
{
  delete [] shareBuf;
  pthread_cond_destroy(&importWriteCondition);
  pthread_mutex_destroy(&importWriteMutex);
  pthread_cond_destroy(&importReadCondition);
  pthread_mutex_destroy(&importReadMutex);
  pthread_mutex_destroy(&importMutex);
}

long AudioBuffer :: getSamplesQueued()
{
  long n = 0;
  if(pthread_mutex_lock(&importMutex) == 0) {
    if(shareBufStart <= shareBufEnd) {
      n = shareBufEnd-shareBufStart;
    } else {
      n = shareBufSize-shareBufStart + shareBufEnd;
    }
  } 
  pthread_mutex_unlock(&importMutex);
  return n;
}

void AudioBuffer :: writingComplete()
{
  if(pthread_mutex_lock(&importMutex) == 0) {
    bReadFlush = true;
    pthread_cond_broadcast(&importReadCondition);
    pthread_mutex_unlock(&importMutex);
  }
}

void AudioBuffer :: readingComplete()
{
  if(pthread_mutex_lock(&importMutex) == 0) {
    shareBufStart = shareBufEnd;
    bReadFlush = false;
    pthread_cond_broadcast(&importWriteCondition);
    pthread_mutex_unlock(&importMutex);
  }
}

void AudioBuffer :: flush()
{
  if(pthread_mutex_lock(&importMutex) == 0) {
    shareBufStart = 0;
    shareBufEnd = 0;
    readBlockSize = 0;
    bReadFlush = false;
    pthread_mutex_unlock(&importMutex);
  }
}

bool AudioBuffer :: isReadReady()
{
  if(bReadFlush) return true;
  if(shareBufStart <= shareBufEnd) 
    return (shareBufEnd-shareBufStart >= readBlockSize);
  else
    return (shareBufSize-shareBufStart + shareBufEnd >= readBlockSize);
}

bool AudioBuffer :: isWriteReady() 
{
  if(shareBufStart <= shareBufEnd) {
     return (shareBufEnd-shareBufStart < halfShareBufSize);
  } else {
     return (shareBufStart-shareBufEnd >= halfShareBufSize);
  }
}

bool AudioBuffer :: isFull()
{
  bool bFull = false;
  if(pthread_mutex_lock(&importMutex) == 0) {
    bFull = !isWriteReady();
    pthread_mutex_unlock(&importMutex);
  }  
  return bFull;
}

long AudioBuffer :: read(float *outputBuffer, long block_size) 
{
  long n_toread = block_size;
  long nDoneNow = 0;

  if(pthread_mutex_lock(&importReadMutex) == 0) {

    bool bReady = false;
    while(!bReady) {
      if(pthread_mutex_lock(&importMutex) == 0) {
        readBlockSize = block_size;
        bReady = isReadReady();
        readBlockSize = 0;
        if(!bReady) {
          pthread_cond_wait(&importReadCondition, &importMutex);
        }
        pthread_mutex_unlock(&importMutex);
      }
    }

    if(pthread_mutex_lock(&importMutex) == 0) {
      if(bReadFlush) {
        if(shareBufStart <= shareBufEnd) {
          n_toread = min(n_toread,shareBufEnd-shareBufStart);
        } else {
          n_toread = min(n_toread,shareBufSize-shareBufStart + shareBufEnd);
        }
      }
      if(shareBufStart <= shareBufEnd) {
        n_toread = min(n_toread, shareBufEnd-shareBufStart);
        copy(outputBuffer,0,shareBuf,shareBufStart,n_toread);
        nDoneNow += n_toread;
      } else {
        n_toread = min(n_toread, shareBufSize-shareBufStart);
        copy(outputBuffer,0,shareBuf,shareBufStart,n_toread);
        nDoneNow += n_toread;
        n_toread = block_size - nDoneNow;
        n_toread = min(n_toread, shareBufEnd);
        copy(outputBuffer,nDoneNow,shareBuf,0,n_toread);
        nDoneNow += n_toread;
      }
      
      shareBufStart += nDoneNow;  
      shareBufStart %= shareBufSize;
      
      if(isWriteReady()) {
        pthread_cond_broadcast(&importWriteCondition);
      }
      
      pthread_mutex_unlock(&importMutex);
    }
    pthread_mutex_unlock(&importReadMutex);
  }
  
  return nDoneNow;  
}

long AudioBuffer :: write(float *buf, long n)
{
  assert(n<=halfShareBufSize);

  long n_written=0, n_towrite=0;

  if(pthread_mutex_lock(&importWriteMutex) == 0) {

    bool bReady = false;
    while(!bReady) {
      if(pthread_mutex_lock(&importMutex) == 0) {
        bReady = isWriteReady();
        if(!bReady) {
          pthread_cond_wait(&importWriteCondition, &importMutex);
        }
        pthread_mutex_unlock(&importMutex);
      }
    }

    if(pthread_mutex_lock(&importMutex) == 0) {
      n_towrite = min(n,shareBufSize-shareBufEnd);
      copy(shareBuf,shareBufEnd,buf,n_written,n_towrite);
      shareBufEnd += n_towrite;
      n_written = n_towrite;
      n_towrite = n - n_written;
      
      if(n_towrite) {
        shareBufEnd = 0;
        copy(shareBuf,shareBufEnd,buf,n_written,n_towrite);
        shareBufEnd += n_towrite;
        n_written += n_towrite;
      }
      
      shareBufEnd %= shareBufSize;

      if(isReadReady()) {
        pthread_cond_broadcast(&importReadCondition);
      }
      pthread_mutex_unlock(&importMutex);
    }
    pthread_mutex_unlock(&importWriteMutex);
  }
  return n_written;
}
