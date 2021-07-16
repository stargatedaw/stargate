""" Created using h2xml and xml2py """

from ctypes import *

STRING = c_char_p


pmBufferMaxSize = -9992
pmBadPtr = -9995
pmInternalError = -9993
pmBadData = -9994
pmNoData = 0
pmBufferTooSmall = -9997
pmInsufficientMemory = -9998
pmBufferOverflow = -9996
pmInvalidDeviceId = -9999
pmHostError = -10000
pmGotData = 1
pmNoError = 0

# values for enumeration 'PmError'
PmError = c_int # enum
PortMidiStream = None
PmDeviceID = c_int
class PmDeviceInfo(Structure):
    pass
PmDeviceInfo._fields_ = [
    ('structVersion', c_int),
    ('interf', STRING),
    ('name', STRING),
    ('input', c_int),
    ('output', c_int),
    ('opened', c_int),
]
int32_t = c_int32
PmTimestamp = int32_t
PmTimeProcPtr = CFUNCTYPE(PmTimestamp, c_void_p)
PmMessage = int32_t
class PmEvent(Structure):
    pass
PmEvent._fields_ = [
    ('message', PmMessage),
    ('timestamp', PmTimestamp),
]
int8_t = c_int8
int16_t = c_int16
int64_t = c_int64
uint8_t = c_uint8
uint16_t = c_uint16
uint32_t = c_uint32
uint64_t = c_uint64
int_least8_t = c_byte
int_least16_t = c_short
int_least32_t = c_int
int_least64_t = c_long
uint_least8_t = c_ubyte
uint_least16_t = c_ushort
uint_least32_t = c_uint
uint_least64_t = c_ulong
int_fast8_t = c_byte
int_fast16_t = c_long
int_fast32_t = c_long
int_fast64_t = c_long
uint_fast8_t = c_ubyte
uint_fast16_t = c_ulong
uint_fast32_t = c_ulong
uint_fast64_t = c_ulong
intptr_t = c_long
uintptr_t = c_ulong
intmax_t = c_long
uintmax_t = c_ulong
__all__ = ['PmTimeProcPtr', 'pmBadPtr', 'pmInsufficientMemory',
           'PmError', 'PmMessage', 'uintptr_t', 'uintmax_t',
           'int_fast32_t', 'int16_t', 'int64_t', 'int_fast16_t',
           'PmTimestamp', 'pmInvalidDeviceId', 'int_fast64_t',
           'uint_least16_t', 'PmDeviceID', 'uint8_t', 'pmGotData',
           'uint_fast16_t', 'int_least8_t', 'pmHostError', 'PmEvent',
           'pmBufferOverflow', 'uint_least32_t', 'int_least64_t',
           'int_least16_t', 'int32_t', 'uint_least8_t', 'pmNoError',
           'intptr_t', 'PmDeviceInfo', 'uint_fast64_t',
           'uint_least64_t', 'int_least32_t', 'int8_t',
           'pmBufferTooSmall', 'int_fast8_t', 'pmBufferMaxSize',
           'uint_fast32_t', 'pmInternalError', 'pmBadData',
           'intmax_t', 'PortMidiStream', 'pmNoData', 'uint32_t',
           'uint64_t', 'uint16_t', 'uint_fast8_t']
