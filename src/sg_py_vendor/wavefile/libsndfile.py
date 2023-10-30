"""
A (currently) limited wrapper around the library libsndfile by Erik Castro de Lopo

http://www.mega-nerd.com/libsndfile/

licensed under the LGPL
(http://www.gnu.org/copyleft/lesser.html)

All sounds formats supported by libsndfile are available and a class interface
is implemented with some helper methods.

Requires numpy and ctypes. Tested under windows only.
"""

import os
import sys
import ctypes as ct
import numpy as np

IS_WINDOWS = "win32" in sys.platform or "msys" in sys.platform

if sys.platform == "win32":
    dllName = 'libsndfile-1'
elif "linux" in sys.platform:
    dllName = 'libsndfile.so.1'
elif "cygwin" in sys.platform:
    dllName = 'libsndfile-1.dll'
elif "darwin" in sys.platform:
    dllName = 'libsndfile.1.dylib'
else:
    dllName = 'libsndfile'

print(sys.platform)
print(dllName)

_lib=None
try:
    from ctypes.util import find_library
    #does the user already have libsamplerate installed?
    if sys.platform == 'win32' :
        dllPath = find_library(dllName)
        # Stargate hack to locate development folder of dlls
        if dllPath is None:
            dllPath = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    '..',
                    'engine',
                    'libsndfile-1.dll',
                ),
            )
    else :
        dllPath = dllName
    print(dllPath)
    _lib = ct.CDLL(dllPath)
except Exception as ex:
    print(f'Could not load {dllPath}: {ex}')

if not _lib:
    try:
        #if not, get the dll installed with the wrapper
        dllPath = os.path.dirname(os.path.abspath(__file__))
        _lib = ct.CDLL(os.path.join(dllPath, dllName))
    except Exception as ex:
        print(f'Could not load {dllPath}: {ex}')

if not _lib:
    try:
        dllPath = os.path.dirname(os.path.abspath(sys.executable))
        dllPath = os.path.join(dllPath, 'engine', dllName)
        print(dllPath)
        _lib = ct.CDLL(dllPath)
    except Exception as ex:
        print(f'Could not load {dllPath}: {ex}')

if not _lib:
    raise Exception(
        f"could not import libsndfile dll, make sure the dll '{dllName}' "
        "is in the path"
    )

_lib.sf_version_string.restype = ct.c_char_p
_lib.sf_version_string.argtypes = None
#print "libsndfile loaded version:", _lib.sf_version_string()



class FILE_FORMATS():

    # Major formats
    SF_FORMAT_WAV        = 0x010000    # Microsoft WAV format (little endian default).
    SF_FORMAT_AIFF       = 0x020000    # Apple/SGI AIFF format (big endian).
    SF_FORMAT_AU         = 0x030000    # Sun/NeXT AU format (big endian).
    SF_FORMAT_RAW        = 0x040000    # RAW PCM data.
    SF_FORMAT_PAF        = 0x050000    # Ensoniq PARIS file format.
    SF_FORMAT_SVX        = 0x060000    # Amiga IFF / SVX8 / SV16 format.
    SF_FORMAT_NIST       = 0x070000    # Sphere NIST format.
    SF_FORMAT_VOC        = 0x080000    # VOC files.
    SF_FORMAT_IRCAM      = 0x0A0000    # Berkeley/IRCAM/CARL
    SF_FORMAT_W64        = 0x0B0000    # Sonic Foundry's 64 bit RIFF/WAV
    SF_FORMAT_MAT4       = 0x0C0000    # Matlab (tm) V4.2 / GNU Octave 2.0
    SF_FORMAT_MAT5       = 0x0D0000    # Matlab (tm) V5.0 / GNU Octave 2.1
    SF_FORMAT_PVF        = 0x0E0000    # Portable Voice Format
    SF_FORMAT_XI         = 0x0F0000    # Fasttracker 2 Extended Instrument
    SF_FORMAT_HTK        = 0x100000    # HMM Tool Kit format
    SF_FORMAT_SDS        = 0x110000    # Midi Sample Dump Standard
    SF_FORMAT_AVR        = 0x120000    # Audio Visual Research
    SF_FORMAT_WAVEX      = 0x130000    # MS WAVE with WAVEFORMATEX
    SF_FORMAT_SD2        = 0x160000    # Sound Designer 2
    SF_FORMAT_FLAC       = 0x170000    # FLAC lossless file format
    SF_FORMAT_CAF        = 0x180000    # Core Audio File format
    SF_FORMAT_WVE        = 0x190000    # Psion WVE format
    SF_FORMAT_OGG        = 0x200000    # Xiph OGG container
    SF_FORMAT_MPC2K      = 0x210000    # Akai MPC 2000 sampler
    SF_FORMAT_RF64       = 0x220000    # RF64 WAV file

    # Subtypes from here on.

    SF_FORMAT_PCM_S8     = 0x0001    # Signed 8 bit data
    SF_FORMAT_PCM_16     = 0x0002    # Signed 16 bit data
    SF_FORMAT_PCM_24     = 0x0003    # Signed 24 bit data
    SF_FORMAT_PCM_32     = 0x0004    # Signed 32 bit data

    SF_FORMAT_PCM_U8     = 0x0005    # Unsigned 8 bit data (WAV and RAW only)

    SF_FORMAT_FLOAT      = 0x0006    # 32 bit float data
    SF_FORMAT_DOUBLE     = 0x0007    # 64 bit float data

    SF_FORMAT_ULAW       = 0x0010    # U-Law encoded.
    SF_FORMAT_ALAW       = 0x0011    # A-Law encoded.
    SF_FORMAT_IMA_ADPCM  = 0x0012    # IMA ADPCM.
    SF_FORMAT_MS_ADPCM   = 0x0013    # Microsoft ADPCM.

    SF_FORMAT_GSM610     = 0x0020    # GSM 6.10 encoding.
    SF_FORMAT_VOX_ADPCM  = 0x0021    # OKI / Dialogix ADPCM

    SF_FORMAT_G721_32    = 0x0030    # 32kbs G721 ADPCM encoding.
    SF_FORMAT_G723_24    = 0x0031    # 24kbs G723 ADPCM encoding.
    SF_FORMAT_G723_40    = 0x0032    # 40kbs G723 ADPCM encoding.

    SF_FORMAT_DWVW_12    = 0x0040    # 12 bit Delta Width Variable Word encoding.
    SF_FORMAT_DWVW_16    = 0x0041    # 16 bit Delta Width Variable Word encoding.
    SF_FORMAT_DWVW_24    = 0x0042    # 24 bit Delta Width Variable Word encoding.
    SF_FORMAT_DWVW_N     = 0x0043    # N bit Delta Width Variable Word encoding.

    SF_FORMAT_DPCM_8     = 0x0050    # 8 bit differential PCM (XI only)
    SF_FORMAT_DPCM_16    = 0x0051    # 16 bit differential PCM (XI only)

    SF_FORMAT_VORBIS     = 0x0060    # Xiph Vorbis encoding.

    SF_FORMAT_ALAC_16    = 0x0070    # Apple Lossless Audio Codec (16 bit)
    SF_FORMAT_ALAC_20    = 0x0071    # Apple Lossless Audio Codec (20 bit)
    SF_FORMAT_ALAC_24    = 0x0072    # Apple Lossless Audio Codec (24 bit)
    SF_FORMAT_ALAC_32    = 0x0073    # Apple Lossless Audio Codec (32 bit)

    # Endian-ness options.

    SF_ENDIAN_FILE       = 0x00000000    # Default file endian-ness.
    SF_ENDIAN_LITTLE     = 0x10000000    # Force little endian-ness.
    SF_ENDIAN_BIG        = 0x20000000    # Force big endian-ness.
    SF_ENDIAN_CPU        = 0x30000000    # Force CPU endian-ness.

    SF_FORMAT_SUBMASK    = 0x0000FFFF
    SF_FORMAT_TYPEMASK   = 0x0FFF0000
    SF_FORMAT_ENDMASK    = 0x30000000


# String types that can be set and read from files. Not all file types
# support this and even the file types which support one, may not support
# all string types.
class FILE_STRINGS():
    SF_STR_TITLE       = 0x01
    SF_STR_COPYRIGHT   = 0x02
    SF_STR_SOFTWARE    = 0x03
    SF_STR_ARTIST      = 0x04
    SF_STR_COMMENT     = 0x05
    SF_STR_DATE        = 0x06
    SF_STR_ALBUM       = 0x07
    SF_STR_LICENSE     = 0x08
    SF_STR_TRACKNUMBER = 0x09
    SF_STR_GENRE       = 0x10

# Public error values. These are guaranteed to remain unchanged for the duration
# of the library major version number.
# There are also a large number of private error numbers which are internal to
# the library which can change at any time.
SF_ERR_NO_ERROR             = 0
SF_ERR_UNRECOGNISED_FORMAT  = 1
SF_ERR_SYSTEM               = 2
SF_ERR_MALFORMED_FILE       = 3
SF_ERR_UNSUPPORTED_ENCODING = 4

class AMBISONICS:
    SF_AMBISONIC_NONE      = 0x40
    SF_AMBISONIC_B_FORMAT  = 0x41

class CHANNEL_MAP:
    SF_CHANNEL_MAP_INVALID               = 0
    SF_CHANNEL_MAP_MONO                  = 1
    SF_CHANNEL_MAP_LEFT                  = 2  # Apple calls this 'Left'
    SF_CHANNEL_MAP_RIGHT                 = 3  # Apple calls this 'Right'
    SF_CHANNEL_MAP_CENTER                = 4  # Apple calls this 'Center'
    SF_CHANNEL_MAP_FRONT_LEFT            = 5
    SF_CHANNEL_MAP_FRONT_RIGHT           = 6
    SF_CHANNEL_MAP_FRONT_CENTER          = 7
    SF_CHANNEL_MAP_REAR_CENTER           = 8  # Apple calls this 'Center Surround', Msft calls this 'Back Center'
    SF_CHANNEL_MAP_REAR_LEFT             = 9  # Apple calls this 'Left Surround', Msft calls this 'Back Left'
    SF_CHANNEL_MAP_REAR_RIGHT            = 10 # Apple calls this 'Right Surround', Msft calls this 'Back Right'
    SF_CHANNEL_MAP_LFE                   = 11 # Apple calls this 'LFEScreen', Msft calls this 'Low Frequency'
    SF_CHANNEL_MAP_FRONT_LEFT_OF_CENTER  = 12 # Apple calls this 'Left Center'
    SF_CHANNEL_MAP_FRONT_RIGHT_OF_CENTER = 13 # Apple calls this 'Right Center'
    SF_CHANNEL_MAP_SIDE_LEFT             = 14 # Apple calls this 'Left Surround Direct' */
    SF_CHANNEL_MAP_SIDE_RIGHT            = 15 # Apple calls this 'Right Surround Direct' */
    SF_CHANNEL_MAP_TOP_CENTER            = 16 # Apple calls this 'Top Center Surround' */
    SF_CHANNEL_MAP_TOP_FRONT_LEFT        = 17 # Apple calls this 'Vertical Height Left' */
    SF_CHANNEL_MAP_TOP_FRONT_RIGHT       = 18 # Apple calls this 'Vertical Height Right' */
    SF_CHANNEL_MAP_TOP_FRONT_CENTER      = 19 # Apple calls this 'Vertical Height Center' */
    SF_CHANNEL_MAP_TOP_REAR_LEFT         = 20 # Apple and MS call this 'Top Back Left' */
    SF_CHANNEL_MAP_TOP_REAR_RIGHT        = 21 # Apple and MS call this 'Top Back Right' */
    SF_CHANNEL_MAP_TOP_REAR_CENTER       = 22 # Apple and MS call this 'Top Back Center' */

    SF_CHANNEL_MAP_AMBISONIC_B_W = 23
    SF_CHANNEL_MAP_AMBISONIC_B_X = 24
    SF_CHANNEL_MAP_AMBISONIC_B_Y = 25
    SF_CHANNEL_MAP_AMBISONIC_B_Z = 26
    SF_CHANNEL_MAP_MAX           = 27

#  The following are the valid command numbers for the sf_command()
#  interface.  The use of these commands is documented in the file
#  command.html in the doc directory of the source code distribution.
class COMMANDS:
    SFC_GET_LIB_VERSION            = 0x1000
    SFC_GET_LOG_INFO               = 0x1001
    SFC_GET_CURRENT_SF_INFO        = 0x1002


    SFC_GET_NORM_DOUBLE            = 0x1010
    SFC_GET_NORM_FLOAT             = 0x1011
    SFC_SET_NORM_DOUBLE            = 0x1012
    SFC_SET_NORM_FLOAT             = 0x1013
    SFC_SET_SCALE_FLOAT_INT_READ   = 0x1014
    SFC_SET_SCALE_INT_FLOAT_WRITE  = 0x1015

    SFC_GET_SIMPLE_FORMAT_COUNT    = 0x1020
    SFC_GET_SIMPLE_FORMAT          = 0x1021

    SFC_GET_FORMAT_INFO            = 0x1028

    SFC_GET_FORMAT_MAJOR_COUNT     = 0x1030
    SFC_GET_FORMAT_MAJOR           = 0x1031
    SFC_GET_FORMAT_SUBTYPE_COUNT   = 0x1032
    SFC_GET_FORMAT_SUBTYPE         = 0x1033

    SFC_CALC_SIGNAL_MAX            = 0x1040
    SFC_CALC_NORM_SIGNAL_MAX       = 0x1041
    SFC_CALC_MAX_ALL_CHANNELS      = 0x1042
    SFC_CALC_NORM_MAX_ALL_CHANNELS = 0x1043
    SFC_GET_SIGNAL_MAX             = 0x1044
    SFC_GET_MAX_ALL_CHANNELS       = 0x1045

    SFC_SET_ADD_PEAK_CHUNK         = 0x1050
    SFC_SET_ADD_HEADER_PAD_CHUNK   = 0x1051

    SFC_UPDATE_HEADER_NOW          = 0x1060
    SFC_SET_UPDATE_HEADER_AUTO     = 0x1061

    SFC_FILE_TRUNCATE              = 0x1080

    SFC_SET_RAW_START_OFFSET       = 0x1090

    SFC_SET_DITHER_ON_WRITE        = 0x10A0
    SFC_SET_DITHER_ON_READ         = 0x10A1

    SFC_GET_DITHER_INFO_COUNT      = 0x10A2
    SFC_GET_DITHER_INFO            = 0x10A3

    SFC_GET_EMBED_FILE_INFO        = 0x10B0

    SFC_SET_CLIPPING               = 0x10C0
    SFC_GET_CLIPPING               = 0x10C1

    SFC_GET_INSTRUMENT             = 0x10D0
    SFC_SET_INSTRUMENT             = 0x10D1

    SFC_GET_LOOP_INFO              = 0x10E0

    SFC_GET_BROADCAST_INFO         = 0x10F0
    SFC_SET_BROADCAST_INFO         = 0x10F1

    SFC_GET_CHANNEL_MAP_INFO       = 0x1100
    SFC_SET_CHANNEL_MAP_INFO       = 0x1101

    SFC_RAW_DATA_NEEDS_ENDSWAP     = 0x1110

    # Support for Wavex Ambisonics Format
    SFC_WAVEX_SET_AMBISONIC        = 0x1200
    SFC_WAVEX_GET_AMBISONIC        = 0x1201

    # RF64, if <4Gb, on save, use regular RIFF/WAV
    SFC_RF64_AUTO_DOWNGRADE        = 0x1210

    SFC_SET_VBR_ENCODING_QUALITY   = 0x1300
    SFC_SET_COMPRESSION_LEVEL      = 0x1301

    # Cart Chunk support
    SFC_SET_CART_INFO              = 0x1400
    SFC_GET_CART_INFO              = 0x1401

    # Following commands for testing only.
    SFC_TEST_IEEE_FLOAT_REPLACE    = 0x6001


    # SFC_SET_ADD_* values are deprecated and will disappear at some
    # time in the future. They are guaranteed to be here up to and
    # including version 1.0.8 to avoid breakage of existing software.
    # They currently do nothing and will continue to do nothing.

    SFC_SET_ADD_DITHER_ON_WRITE    = 0x1070
    SFC_SET_ADD_DITHER_ON_READ     = 0x1071


#other definitions :
sf_count_t = ct.c_int64


#structs:
class SF_INFO(ct.Structure):
    _fields_ = [
        ("frames", sf_count_t), #Used to be called samples.  Changed to avoid confusion.
        ("samplerate", ct.c_int),
        ("channels", ct.c_int),
        ("format", ct.c_int),
        ("sections", ct.c_int),
        ("seekable", ct.c_int)
    ]

def __init_lib_methods():
    SNDFILE = ct.c_void_p

    #SNDFILE*     sf_open        (const char *path, int mode, SF_INFO *sfinfo);
    _lib.sf_open.restype = SNDFILE
    _lib.sf_open.argtypes = [ct.c_char_p, ct.c_int, ct.POINTER(SF_INFO)]

    if IS_WINDOWS:
        #SNDFILE*     sf_wchar_open  (LPCWSTR wpath, int mode, SF_INFO *sfinfo);
        _lib.sf_wchar_open.restype = SNDFILE
        _lib.sf_wchar_open.argtypes = [ct.c_wchar_p, ct.c_int, ct.POINTER(SF_INFO)]

    #int        sf_error        (SNDFILE *sndfile) ;
    _lib.sf_error.restype = ct.c_int
    _lib.sf_error.argtypes = [SNDFILE]

    #const char* sf_strerror (SNDFILE *sndfile) ;
    _lib.sf_strerror.restype = ct.c_char_p
    _lib.sf_strerror.argtypes = [SNDFILE]

    #const char* sf_error_number (int ) ;
    _lib.sf_error_number.restype = ct.c_char_p
    _lib.sf_error_number.argtypes = [ct.c_int]

    #int        sf_format_check    (const SF_INFO *info) ;
    _lib.sf_format_check.restype = ct.c_int
    _lib.sf_format_check.argtypes = [ct.POINTER(SF_INFO)]

    #sf_count_t    sf_seek         (SNDFILE *sndfile, sf_count_t frames, int whence) ;
    _lib.sf_seek.restype = sf_count_t
    _lib.sf_seek.argtypes = [SNDFILE, sf_count_t, ct.c_int]

    #const char* sf_get_string (SNDFILE *sndfile, int str_type) ;
    _lib.sf_get_string.restype = ct.c_char_p
    _lib.sf_get_string.argtypes = [SNDFILE, ct.c_int]

    #int         sf_set_string    (SNDFILE *sndfile, int str_type, const char* str) ;
    #TODO
    _lib.sf_set_string.restype = ct.c_int
    _lib.sf_set_string.argtypes = [SNDFILE, ct.c_int, ct.c_char_p]

    #sf_count_t    sf_read_raw        (SNDFILE *sndfile, void *ptr, sf_count_t bytes) ;
    _lib.sf_read_raw.restype = sf_count_t
    _lib.sf_read_raw.argtypes = [SNDFILE, ct.c_void_p, sf_count_t]

    # Functions for reading and writing the data chunk in terms of frames.
    # The number of items actually read/written = frames * number of channels.
    #     sf_xxxx_raw        read/writes the raw data bytes from/to the file
    #     sf_xxxx_short    passes data in the native short format
    #     sf_xxxx_int        passes data in the native int format
    #     sf_xxxx_float    passes data in the native float format
    #     sf_xxxx_double    passes data in the native double format
    # All of these read/write function return number of frames read/written.
    #sf_count_t    sf_readf_float    (SNDFILE *sndfile, float *ptr, sf_count_t frames) ;
    _lib.sf_read_float.restype = sf_count_t
    _lib.sf_read_float.argtypes = [SNDFILE, ct.POINTER(ct.c_float), sf_count_t]
    _lib.sf_read_double.restype = sf_count_t
    _lib.sf_read_double.argtypes = [SNDFILE, ct.POINTER(ct.c_double), sf_count_t]
    _lib.sf_read_short.restype = sf_count_t
    _lib.sf_read_short.argtypes = [SNDFILE, ct.POINTER(ct.c_short), sf_count_t]
    _lib.sf_read_int.restype = sf_count_t
    _lib.sf_read_int.argtypes = [SNDFILE, ct.POINTER(ct.c_int), sf_count_t]

    _lib.sf_readf_float.restype = sf_count_t
    _lib.sf_readf_float.argtypes = [SNDFILE, ct.POINTER(ct.c_float), sf_count_t]
    _lib.sf_readf_double.restype = sf_count_t
    _lib.sf_readf_double.argtypes = [SNDFILE, ct.POINTER(ct.c_double), sf_count_t]
    _lib.sf_readf_short.restype = sf_count_t
    _lib.sf_readf_short.argtypes = [SNDFILE, ct.POINTER(ct.c_short), sf_count_t]
    _lib.sf_readf_int.restype = sf_count_t
    _lib.sf_readf_int.argtypes = [SNDFILE, ct.POINTER(ct.c_int), sf_count_t]

    #sf_count_t    sf_write_raw     (SNDFILE *sndfile, const void *ptr, sf_count_t bytes) ;
    _lib.sf_write_raw.restype = sf_count_t
    _lib.sf_write_raw.argtypes = [SNDFILE, ct.c_void_p, sf_count_t]

    #int        sf_close        (SNDFILE *sndfile) ;
    _lib.sf_close.restype = ct.c_int
    _lib.sf_close.argtypes = [SNDFILE]

    #writing functions
    #sf_count_t  sf_write_short   (SNDFILE *sndfile, short *ptr, sf_count_t items) ;
    #sf_count_t  sf_write_int     (SNDFILE *sndfile, int *ptr, sf_count_t items) ;
    #sf_count_t  sf_write_float   (SNDFILE *sndfile, float *ptr, sf_count_t items) ;
    #sf_count_t  sf_write_double  (SNDFILE *sndfile, double *ptr, sf_count_t items) ;
    _lib.sf_write_int.restype = sf_count_t
    _lib.sf_write_int.argtypes = [SNDFILE, ct.POINTER(ct.c_int), sf_count_t]
    _lib.sf_write_short.restype = sf_count_t
    _lib.sf_write_short.argtypes = [SNDFILE, ct.POINTER(ct.c_short), sf_count_t]
    _lib.sf_write_float.restype = sf_count_t
    _lib.sf_write_float.argtypes = [SNDFILE, ct.POINTER(ct.c_float), sf_count_t]
    _lib.sf_write_double.restype = sf_count_t
    _lib.sf_write_double.argtypes = [SNDFILE, ct.POINTER(ct.c_double), sf_count_t]

    _lib.sf_writef_int.restype = sf_count_t
    _lib.sf_writef_int.argtypes = [SNDFILE, ct.POINTER(ct.c_int), sf_count_t]
    _lib.sf_writef_short.restype = sf_count_t
    _lib.sf_writef_short.argtypes = [SNDFILE, ct.POINTER(ct.c_short), sf_count_t]
    _lib.sf_writef_float.restype = sf_count_t
    _lib.sf_writef_float.argtypes = [SNDFILE, ct.POINTER(ct.c_float), sf_count_t]
    _lib.sf_writef_double.restype = sf_count_t
    _lib.sf_writef_double.argtypes = [SNDFILE, ct.POINTER(ct.c_double), sf_count_t]

    if _lib.sf_version_string().decode() != 'libsndfile-1.0.25':

        #int sf_current_byterate (SNDFILE *sndfile) ;
        _lib.sf_current_byterate.restype = ct.c_int
        _lib.sf_current_byterate.argtypes = [SNDFILE]

	# TODO: Chunks, new undocumented feature in 1.0.26

	#struct SF_CHUNK_INFO
	#{	char		id [64] ;	/* The chunk identifier. */
	#	unsigned	id_size ;	/* The size of the chunk identifier. */
	#	unsigned	datalen ;	/* The size of that data. */
	#	void		*data ;		/* Pointer to the data. */
	#} ;

	#typedef struct SF_CHUNK_INFO SF_CHUNK_INFO ;
	#int sf_set_chunk (SNDFILE * sndfile, const SF_CHUNK_INFO * chunk_info) ;
	#typedef	struct SF_CHUNK_ITERATOR SF_CHUNK_ITERATOR ;
	#SF_CHUNK_ITERATOR * sf_get_chunk_iterator (SNDFILE * sndfile, const SF_CHUNK_INFO * chunk_info) ;
	#SF_CHUNK_ITERATOR * sf_next_chunk_iterator (SF_CHUNK_ITERATOR * iterator) ;
	#int sf_get_chunk_size (const SF_CHUNK_ITERATOR * it, SF_CHUNK_INFO * chunk_info) ;
	#int sf_get_chunk_data (const SF_CHUNK_ITERATOR * it, SF_CHUNK_INFO * chunk_info) ;

__init_lib_methods()


#class definitions :
class OPEN_MODES():
    SFM_READ  = 0x10
    SFM_WRITE = 0x20
    SFM_RDWR  = 0x30

class SEEK_MODES():
    SF_SEEK_SET = 0
    SF_SEEK_CUR = 1
    SF_SEEK_END = 2

