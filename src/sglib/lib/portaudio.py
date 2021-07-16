""" Created using h2xml and xml2py """

from ctypes import *

STRING = c_char_p

paFloat32        = int(0x00000001)
paInt32          = int(0x00000002)
paInt24          = int(0x00000004)
paInt16          = int(0x00000008)
paInt8           = int(0x00000010)
paUInt8          = int(0x00000020)
paCustomFormat   = int(0x00010000)
paNonInterleaved = int(0x80000000)

paNotInitialized = -10000
paSampleFormatNotSupported = -9994
paHostApiNotFound = -9979
paSoundManager = 4
paInvalidFlag = -9995
paCanNotWriteToAnInputOnlyStream = -9974
paInvalidDevice = -9996
paCanNotReadFromAnOutputOnlyStream = -9975
paJACK = 12
paInvalidSampleRate = -9997
paComplete = 1
paInvalidChannelCount = -9998
paCanNotReadFromACallbackStream = -9977
paALSA = 8
paAbort = 2
paWASAPI = 13
paWDSGS = 11
paCanNotWriteToACallbackStream = -9976
paOutputUnderflowed = -9980
paCoreAudio = 5
paOSS = 7
paMME = 2
paInDevelopment = 0
paInputOverflowed = -9981
paDirectSound = 1
paBadBufferPtr = -9972
paBufferTooSmall = -9990
paStreamIsNotStopped = -9982
paStreamIsStopped = -9983
paIncompatibleHostApiSpecificStreamInfo = -9984
paInternalError = -9986
paNullCallback = -9989
paDeviceUnavailable = -9985
paAudioScienceHPI = 14
paContinue = 0
paInsufficientMemory = -9992
paBufferTooBig = -9991
paIncompatibleStreamHostApi = -9973
paUnanticipatedHostError = -9999
paBadIODeviceCombination = -9993
paNoError = 0
paTimedOut = -9987
paBadStreamPtr = -9988
paAL = 9
paInvalidHostApi = -9978
paASIO = 3
paBeOS = 10
PaError = c_int

# values for enumeration 'PaErrorCode'
PaErrorCode = c_int # enum
PaDeviceIndex = c_int
PaHostApiIndex = c_int

# values for enumeration 'PaHostApiTypeId'
PaHostApiTypeId = c_int # enum
class PaHostApiInfo(Structure):
    pass
PaHostApiInfo._fields_ = [
    ('structVersion', c_int),
    ('type', PaHostApiTypeId),
    ('name', STRING),
    ('deviceCount', c_int),
    ('defaultInputDevice', PaDeviceIndex),
    ('defaultOutputDevice', PaDeviceIndex),
]
class PaHostErrorInfo(Structure):
    pass
PaHostErrorInfo._fields_ = [
    ('hostApiType', PaHostApiTypeId),
    ('errorCode', c_long),
    ('errorText', STRING),
]
PaTime = c_double
PaSampleFormat = c_ulong
class PaDeviceInfo(Structure):
    pass
PaDeviceInfo._fields_ = [
    ('structVersion', c_int),
    ('name', STRING),
    ('hostApi', PaHostApiIndex),
    ('maxInputChannels', c_int),
    ('maxOutputChannels', c_int),
    ('defaultLowInputLatency', PaTime),
    ('defaultLowOutputLatency', PaTime),
    ('defaultHighInputLatency', PaTime),
    ('defaultHighOutputLatency', PaTime),
    ('defaultSampleRate', c_double),
]
class PaStreamParameters(Structure):
    pass
PaStreamParameters._fields_ = [
    ('device', PaDeviceIndex),
    ('channelCount', c_int),
    ('sampleFormat', PaSampleFormat),
    ('suggestedLatency', PaTime),
    ('hostApiSpecificStreamInfo', c_void_p),
]
PaStream = None
PaStreamFlags = c_ulong
class PaStreamCallbackTimeInfo(Structure):
    pass
PaStreamCallbackTimeInfo._fields_ = [
    ('inputBufferAdcTime', PaTime),
    ('currentTime', PaTime),
    ('outputBufferDacTime', PaTime),
]
PaStreamCallbackFlags = c_ulong

# values for enumeration 'PaStreamCallbackResult'
PaStreamCallbackResult = c_int # enum
PaStreamCallback = CFUNCTYPE(c_int, c_void_p, c_void_p, c_ulong, POINTER(PaStreamCallbackTimeInfo), PaStreamCallbackFlags, c_void_p)
PaStreamFinishedCallback = CFUNCTYPE(None, c_void_p)
class PaStreamInfo(Structure):
    pass
PaStreamInfo._fields_ = [
    ('structVersion', c_int),
    ('inputLatency', PaTime),
    ('outputLatency', PaTime),
    ('sampleRate', c_double),
]
__all__ = ['paBadBufferPtr', 'paOSS', 'paInDevelopment',
           'PaDeviceInfo', 'paComplete', 'PaSampleFormat',
           'paHostApiNotFound', 'PaError', 'paASIO', 'paAbort',
           'paIncompatibleStreamHostApi', 'PaStreamParameters',
           'paStreamIsNotStopped', 'PaDeviceIndex',
           'paUnanticipatedHostError', 'PaStreamCallbackTimeInfo',
           'paIncompatibleHostApiSpecificStreamInfo', 'paContinue',
           'paStreamIsStopped', 'paInvalidFlag', 'PaHostApiInfo',
           'PaStreamCallback', 'paInvalidSampleRate',
           'paSoundManager', 'paALSA', 'PaTime', 'paBeOS',
           'paDeviceUnavailable', 'PaStreamCallbackFlags',
           'PaHostApiIndex', 'PaStreamCallbackResult',
           'paInputOverflowed', 'paCanNotReadFromAnOutputOnlyStream',
           'PaStream', 'paAudioScienceHPI', 'paBufferTooSmall',
           'paMME', 'paCanNotWriteToAnInputOnlyStream', 'paWDSGS',
           'PaStreamFlags', 'paDirectSound',
           'paBadIODeviceCombination', 'paTimedOut',
           'paInvalidDevice', 'paWASAPI',
           'paCanNotReadFromACallbackStream', 'paInvalidChannelCount',
           'paJACK', 'paNoError', 'paCoreAudio', 'paNotInitialized',
           'paInsufficientMemory', 'PaErrorCode', 'PaHostApiTypeId',
           'paInternalError', 'paOutputUnderflowed', 'PaStreamInfo',
           'paInvalidHostApi', 'paBufferTooBig', 'paAL',
           'paCanNotWriteToACallbackStream', 'PaHostErrorInfo',
           'PaStreamFinishedCallback', 'paNullCallback',
           'paBadStreamPtr', 'paSampleFormatNotSupported']
