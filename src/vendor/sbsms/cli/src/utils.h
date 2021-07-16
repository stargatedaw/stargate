// -*- mode: c++ -*-
#ifndef UTILS_H
#define UTILS_H

#include "sbsmsx.h"
#include "real.h"
#include "config.h"

namespace _sbsmsx_ {

#define ONEOVERTWOPI 0.15915494309189533576888376337251f
#define PI 3.1415926535897932384626433832795f
#define TWOPI 6.28318530717958647692528676655900576f
 
#ifdef _WIN32
#define FOPEN(fp,fn,mode) fopen_s(&fp,fn,mode)
#else
#define FOPEN(fp,fn,mode) (fp = fopen(fn,mode))
#endif

#ifdef ARCHI386
#undef BIGENDIAN
#endif

#ifdef ARCHPPC
#define BIGENDIAN 1
#endif

#ifdef HAVE_FSEEKO
#define FSEEK fseeko
#define FTELL ftello
#else
#define FSEEK fseek
#define FTELL ftell
#endif

inline uint16 bswap_16(uint16 x) {
  return (x>>8) | (x<<8);
}

inline uint32 bswap_32(uint32 x) {
  return (bswap_16((uint16)(x&0xffff))<<16) | (bswap_16((uint16)(x>>16)));
}

inline uint64 bswap_64(uint64 x) {
  return (((uint64)bswap_32((uint32)(x&0xffffffffull)))<<32) | (bswap_32((uint32)(x>>32)));
}

inline uint16 nativeEndian16(uint16 x)
{
#ifdef BIGENDIAN
	return bswap_16(x);
#else
	return x;
#endif
}

inline uint32 nativeEndian32(uint32 x)
{
#ifdef BIGENDIAN
	return bswap_32(x);
#else
	return x;
#endif
}

inline uint64 nativeEndian64(uint64 x)
{
#ifdef BIGENDIAN
	return bswap_64(x);
#else
	return x;
#endif
}

inline uint16 littleEndian16(uint16 x)
{
#ifdef BIGENDIAN
	return bswap_16(x);
#else
	return x;
#endif
}

inline uint32 littleEndian32(uint32 x)
{
#ifdef BIGENDIAN
	return bswap_32(x);
#else
	return x;
#endif
}

inline uint32 littleEndian64(uint64 x)
{
#ifdef BIGENDIAN
	return bswap_64(x);
#else
	return x;
#endif
}

inline int fread_8_little_endian(FILE *fp) 
{	
  unsigned char y;
  fread(&y,1,1,fp);
  return (int)y;
}

inline int fread_16_little_endian(FILE *fp) 
{
  uint16 y = 0;
  fread(&y,2,1,fp);
  return (int)nativeEndian16(y);
}

inline int32 fread_32_little_endian(FILE *fp) 
{
  uint32 y = 0;
  fread(&y,4,1,fp);
  return (int32)nativeEndian32Int(y);
}

inline int64 fread_64_little_endian(FILE *fp) 
{
  uint64 y = 0LL;
  fread(&y,8,1,fp);
  return (int64)nativeEndian64(y);
}

inline size_t fwrite_8_little_endian(int x, FILE *fp) 
{
  unsigned char y = (unsigned char)x;
  return fwrite(&y,1,1,fp);
}

inline size_t fwrite_16_little_endian(int x, FILE *fp) 
{
  uint16 y = littleEndian16((uint16)x);
  return fwrite(&y,2,1,fp);
}

inline size_t fwrite_32_little_endian(int32 x, FILE *fp) 
{
  uint32 y = littleEndian32((uint32)x);
  return fwrite(&y,4,1,fp);
}

inline size_t fwrite_64_little_endian(int64 x, FILE *fp) 
{
  uint64 y = littleEndian64((uint64)x);
  return fwrite(&y,8,1,fp);	
}

inline float canonPI(float ph) 
{
  ph -= TWOPI * round2int(ph * ONEOVERTWOPI);
  while(ph < -PI) ph += TWOPI;
  while(ph >= PI) ph -= TWOPI;
  return ph;
}

inline float canon2PI(float ph) 
{
  ph -= TWOPI * round2int(ph * ONEOVERTWOPI);
  while(ph < 0.0f) ph += TWOPI;
  while(ph >= TWOPI) ph -= TWOPI;
  return ph;
}

}

#endif
