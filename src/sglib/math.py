try:
    from sg_py_vendor.pymarshal import pm_assert
except ImportError:
    from pymarshal import pm_assert

from math import log, pow
import math
import numpy


__all__ = [
    'clip_max',
    'clip_min',
    'clip_value',
    'color_interpolate',
    'cosine_interpolate',
    'db_to_lin',
    'hz_to_pitch',
    'lin_to_db',
    'linear_interpolate',
    'np_cubic_interpolate',
    'np_linear_interpolate',
    'np_resample',
    'pan_stereo',
    'pitch_to_hz',
    'pitch_to_ratio',
    'quantize',
    'ratio_to_pitch',
    'window_rms',
]

def pitch_to_hz(pitch):
    return (440.0 * pow(2.0, (float(pitch) - 57.0) * 0.0833333))

def hz_to_pitch(hz):
    return ((12.0 * log(float(hz) * (1.0 / 440.0), 2.0)) + 57.0)

def pitch_to_ratio(pitch):
    return (1.0 / pitch_to_hz(0.0)) * pitch_to_hz(float(pitch))

def ratio_to_pitch(ratio):
    base = (pitch_to_hz(0.0))
    hz = base * ratio
    return hz_to_pitch(hz)

def db_to_lin(value):
    return pow(10.0, (0.05 * float(value)))

def lin_to_db(value):
    if value >= 0.001:
        return log(float(value), 10.0) * 20.0
    else:
        return -120.0

def linear_interpolate(point1, point2, frac):
    return ((1.0 - frac) * point1) + (frac * point2)

def cosine_interpolate(y1, y2, mu):
   mu2 = (1.0 - math.cos(mu * math.pi)) / 2
   return(y1 * (1.0 - mu2) + y2 * mu2)

def clip_value(
    val,
    _min,
    _max,
    _round=False,
):
    if val < _min:
        result = _min
    elif val > _max:
        result =  _max
    else:
        result = val
    if _round:
        result = round(result, 6)
    return result

def clip_min(val, _min):
    if val < _min:
        return _min
    else:
        return val

def clip_max(val, _max):
    if val > _max:
        return _max
    else:
        return val

def pan_stereo(
    pan,
    pan_law,
    volume,
):
    """ Calculate left and right channel volume
        @pan:
            float or tuple, The amount of pan -1 to 1.
            If a tuple, values should be in order of precedence first.  The
            first non-None value will be selected.
        @pan_law:
            float, The amount of pan law.  Normal values
            will be 0., -3., or -4.5.
        @volume:
            float, The combined volume of the item reference, in decibels.
            Should be the sum of all volume parameters.

        @return:
            (float, float), The left and right channel, linear (not decibels)
        @raises:
            ValueError: If @pan is outside the range of -1. to 1.
    """
    if isinstance(pan, tuple):
        if all(x is None for x in pan):
            return (
                db_to_lin(volume),
            ) * 2
        else:
            pan = [x for x in pan if x is not None][0]
    pm_assert(
        pan >= -1. and pan <= 1.,
        ValueError,
        pan,
    )
    if pan == 0.:
        return (
            db_to_lin(volume),
        ) * 2
    elif pan < 0.:  # left
        left = pan * pan_law
        right = pan * 24.
        return (
            db_to_lin(left + volume),
            db_to_lin(right + volume),
        )
    else:  # > 0. , right
        left = pan * -24.
        right = pan * pan_law * -1.
        return (
            db_to_lin(left + volume),
            db_to_lin(right + volume),
        )

def np_cubic_interpolate(
    arr,
    pos,
):
    """
        @arr: Numpy array
        @pos: float, The array index to interpolate
    """
    int_pos = clip_value(int(pos), 0, arr.shape[0] - 1)
    mu = pos - float(int_pos)
    mu2 = mu * mu
    int_pos_plus1 = clip_value(int_pos + 1, 0, arr.shape[0] - 1)
    int_pos_minus1 = clip_value(int_pos - 1, 0, arr.shape[0] - 1)
    int_pos_minus2 = clip_value(int_pos - 2, 0, arr.shape[0] - 1)

    a0 = (arr[int_pos_plus1] - arr[int_pos] -
        arr[int_pos_minus2] + arr[int_pos_minus1])
    a1 = arr[int_pos_minus2] - arr[int_pos_minus1] - a0
    a2 = arr[int_pos] - arr[int_pos_minus2]
    a3 = arr[int_pos_minus1]

    return (a0 * mu * mu2 + a1 * mu2 + a2 * mu + a3)

def np_linear_interpolate(
    array,
    pos,
):
    """ Linear interpolation for Numpy arrays
    """
    _int = int(pos)
    frac = pos - _int
    try:
        point1 = array[_int]
        point2 = array[_int + 1]
    except IndexError:
        return array[-1]
    return ((point2 - point1) * frac) + point1

def np_resample(array, new_size):
    new_size = int(new_size) + 1
    result = numpy.zeros(new_size)
    _len = array.shape[0]
    stride = float(_len) / new_size
    pos = 0.0
    for i in range(new_size):
        result[i] = np_linear_interpolate(array, pos)
        pos += stride
    return result

def window_rms(arr, window_size):
  a2 = numpy.power(arr, 2)
  window = numpy.ones(window_size) / float(window_size)
  return numpy.sqrt(numpy.convolve(a2, window, 'valid'))

def quantize(
    pos,
    amt,
):
    """ Quantize @pos to @amt
        @pos:
            float, The unquantized position to quantize
        @amt:
            float, The number of beats to quantize to.
            1.==1/4
            .5==1/8
            .25==1/16
    """
    if (
        not pos
        or
        not amt
    ):
        return pos
    recip = 1. / amt
    pos = round(pos / amt)
    pos *= amt
    return pos

def color_interpolate(
    foreground: str,
    background: str,
    pos: float,
):
    """ Interpolate 2 hex colors.
        Only 6 digit are supported (with or without #), no transparency

        @pos: 0.0 pure foreground to 1.0 pure background
    """
    if foreground.startswith('#'):
        foreground = foreground[1:]
    if background.startswith('#'):
        background = background[1:]
    for x in (foreground, background):
        assert len(x) == 6, f"Invalid hex color {x}"
    assert pos >= 0. and pos <= 1., pos
    result = ""
    for i in range(3):
        fg = float(int(foreground[i*2:(i*2)+2], 16))
        bg = float(int(background[i*2:(i*2)+2], 16))
        color = ((fg - bg) * pos) + bg
        result += hex(int(color))[2:]
    return f"#{result}"

