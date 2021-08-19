from sglib.math import *
import numpy


def test_pitch_to_hz_to_pitch():
    for hz, pitch in (
        (57, 440),
        (45, 220),
        (69, 880),
    ):
        result = round(
            pitch_to_hz(hz),
            3,
        )
        assert result == pitch, (result, pitch)
        result2 = round(
            hz_to_pitch(pitch),
            3,
        )
        assert result2 == hz, (result2, hz)

def test_pitch_to_ratio_to_pitch():
    for pitch, ratio in (
        (0, 1),
        (12, 2),
        (24, 4),
        (-12, .5),
    ):
        _ratio = round(
            pitch_to_ratio(pitch),
            3,
        )
        assert _ratio == _ratio, (_ratio, ratio)
        _pitch = round(
            ratio_to_pitch(ratio),
            3,
        )
        assert _pitch == pitch, (_pitch, pitch)

def test_db_to_lin_to_db():
    for db, lin in (
        (0, 1),
        (-6, .5),
        (6, 2),
    ):
        _lin = round(
            db_to_lin(db),
            1,
        )
        assert _lin == lin, (_lin, lin)
        _db = round(
            lin_to_db(lin),
            1,
        )
        assert _db == db, (_db, db)

def test_lin_to_db_zero():
    assert lin_to_db(0.) == -120.

def test_linear_interpolate():
    result = linear_interpolate(0., 2., .75)
    assert result == 1.5, result

def test_cosine_interpolate():
    result = round(
        cosine_interpolate(0., 1., .5),
        3,
    )
    assert result == .5, result

def test_clip_value():
    for args, expected in (
        ((0, 1, 2, True), 1),
        ((3, 1, 2, True), 2),
        ((2, 1, 3, True), 2),
    ):
        result = clip_value(*args)
        assert result == expected, (result, expected)

def test_clip_min():
    for args, expected in (
        ((0, 0), 0),
        ((1, 2), 2),
    ):
        result = clip_min(*args)
        assert result == expected, (result, expected)

def test_clip_max():
    for args, expected in (
        ((0, 0), 0),
        ((1, 0), 0),
    ):
        result = clip_max(*args)
        assert result == expected, (result, expected)

def test_stereo_pan_center():
    for args, expected in (
        ((0., 0., 0.), (1., 1.)),
        (((None, None,), 0., 0.), (1., 1.)),
        (((None, None, 0.), 0., 0.), (1., 1.)),
    ):
        result = pan_stereo(*args)
        assert result == expected, (args, result, expected)

def test_stereo_pan_left():
    left, right = pan_stereo(-1., -3., -3.)
    assert round(left, 2) == 1., left
    assert round(right, 2) == 0.04, right

def test_stereo_pan_right():
    left, right = pan_stereo(1., -3., -3.)
    assert round(right, 2) == 1., right
    assert round(left, 2) == 0.04, left

def test_np_cubic_interpolate():
    arr = numpy.array([float(x) for x in range(10)])
    result = np_cubic_interpolate(arr, 4.5)
    assert result == 3.5, result

def test_np_linear_interpolate_index_error():
    arr = numpy.array([float(x) for x in range(10)])
    result = np_linear_interpolate(arr, 15)
    assert result == 9., result

def test_np_resample():
    arr = numpy.array([float(x) for x in range(10)])
    resampled = np_resample(arr, 6)
    assert len(resampled) == 7  # + 1

def test_window_rms():
    arr = numpy.array([float(x) for x in range(10)])
    window_rms(arr, 3)

def test_quantize():
    for pos, amt, expected in (
        (0., .5, 0.),
        (2.75, 1., 3.),
        (.68, .25, .75),
        (5.26, .125, 5.25),
        (.3345, 0., .3345),
    ):
        result = quantize(pos, amt)
        assert result == expected, result

def test_color_interpolate():
    for args, expected in (
        (("ffffff", "000000", 0.5), "#7f7f7f"),
        (("#ffffff", "#000000", 0.5), "#7f7f7f"),
    ):
        assert color_interpolate(*args) == expected, (args, expected)

