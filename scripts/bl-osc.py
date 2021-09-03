#!/usr/bin/env python3
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

# This script generates band-limited wavetables of classic waveforms using
# numpy, and converts the wavetables to C code

import numpy
from matplotlib import pyplot

import os
import sys

current_dir = os.path.dirname(__file__)
wavefile_path = os.path.join(current_dir, "..", "src", "py_vendor")
sys.path.append(os.path.abspath(wavefile_path))
import wavefile

CODE_DIR = os.path.abspath(
    os.path.join(
        current_dir,
        "..",
        "src",
        "engine",
        "src",
        "audiodsp",
        "modules",
        "oscillator",
        "af",
    ),
)

SR = 44100.
NYQUIST = SR / 2.

BOILERPLATE = """\
/*
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef {NAMEU}_H
#define {NAMEU}_H

#define AF_{NAMEU}_DCOUNT {DCOUNT}
#define AF_{NAMEU}_WCOUNT {WCOUNT}

__thread int AF_{NAMEU}_INDICES[AF_{NAMEU}_WCOUNT][2] = {{

{WINDICES}

}} __attribute__((aligned(CACHE_LINE_SIZE)));

__thread float AF_{NAMEU}_DATA[AF_{NAMEU}_DCOUNT] = {{

{WDATA}

}} __attribute__((aligned(CACHE_LINE_SIZE)));

#endif /*{NAMEU}_H*/
"""

def pitch_to_hz(a_pitch):
    return (440.0 * pow(2.0, (float(a_pitch) - 57.0) * 0.0833333333333333333))

def get_harmonic(a_size, a_phase, a_num):
    """ @a_size:  The size of the fundamental frequency
        @a_phase: Phase in radians
        @a_num:   The harmonic number, where the fundamental == 1
    """
    f_lin = numpy.linspace(
        a_phase, (2.0 * numpy.pi * a_num) + a_phase, a_size)
    return numpy.sin(f_lin)

def double_to_c_float(a_double):
    return "{}f".format(round(a_double, 7))

def dict_to_c_code(a_dict, a_name):
    arr_lines = []
    line_arr = []
    index_lines = []
    index_start = 0
    index_end = 0
    line_length = 0
    for k in sorted(a_dict):
        v = list(a_dict[k])
        index_start = index_end + 4
        index_end = index_start + len(v)
        index_lines.append("{{{}, {}}}".format(index_start, index_end))
        index_end += 4
        data = v[-4:] + v + v[:4]
        for fp in data:
            cfloat = double_to_c_float(fp)
            if line_length < 50:
                line_arr.append(cfloat)
                line_length += len(cfloat)
            else:
                arr_lines.append(", ".join(line_arr))
                line_arr = [cfloat]
                line_length = len(cfloat)
        arr_data = ",\n".join(arr_lines)
        index_data = ",\n".join(index_lines)
        code = BOILERPLATE.format(
            NAMEU=a_name.upper(), DCOUNT=index_end, WCOUNT=len(index_lines),
            WINDICES=index_data, WDATA=arr_data)
        code_path = os.path.join(CODE_DIR, "{}.h".format(a_name))
        if not os.path.isdir(CODE_DIR):
            os.mkdir(CODE_DIR)
        with open(code_path, 'w') as fh:
            fh.write(code)

def visualize(a_dict):
    keys = list(sorted(a_dict))
    pyplot.plot(a_dict[keys[0]])
    pyplot.show()

def dict_to_wav(a_dict, a_name):
    keys = list(sorted(a_dict))
    name = "{}.wav".format(a_name)
    with wavefile.WaveWriter(name, channels=1, samplerate=44100,) as writer:
        for key in keys[16:70:3]:
            arr = numpy.array([a_dict[key]])
            count = int(SR / arr.shape[1])
            for i in range(count):
                writer.write(arr)

def normalize(arr):
    buffer_max = numpy.amax(numpy.abs(arr))
    arr *= 1. / buffer_max

def get_notes():
    for note in range(0, 100):
        hz = pitch_to_hz(note)
        # This introduces minor rounding error into the note frequency
        length = round(SR / hz)
        count = int((NYQUIST - hz) // hz)
        yield note, length, count

def get_phase_smear(i):
    return (1. - (1. / float(i))) * numpy.pi * .5933333333333333333

def get_sines():
    result = {}
    total_length = 0
    for note, length, count in get_notes():
        total_length += length
        arr = numpy.zeros(length)
        result[note] = arr
        arr += get_harmonic(length, 0.0, 1)
        normalize(arr)
    print("sine data size: {} bytes".format(total_length * 4))
    return result

def get_saws(a_phase_smear=True, a_ss=False):
    result = {}
    total_length = 0
    for note, length, count in get_notes():
        total_length += length
        arr = numpy.zeros(length)
        result[note] = arr
        for i in range(1, count + 1):
            phase = 0.0 if i % 2 else numpy.pi
            if a_phase_smear:
                phase += get_phase_smear(i)
            amp = 4. if a_ss and i < 4 else float(i)
            arr += get_harmonic(length, phase, i) * (1.0 / amp)
        normalize(arr)
    print("saw data size: {} bytes".format(total_length * 4))
    return result

def get_squares(a_phase_smear=True, a_triangle=False):
    result = {}
    total_length = 0
    for note, length, count in get_notes():
        total_length += length
        arr = numpy.zeros(length)
        result[note] = arr
        tri_eo = False
        for i in range(1, count + 1, 2):
            amp = float(i * i) if a_triangle else float(i)
            if a_triangle:
                phase = numpy.pi if tri_eo else 0.0
                tri_eo = not tri_eo
                if a_phase_smear:
                    phase += get_phase_smear(i)
            else:
                phase = get_phase_smear(i) if a_phase_smear else 0.0
            arr += get_harmonic(length, phase, i) * (1.0 / amp)
    print("{} data size: {} bytes".format(
        "triangle" if a_triangle else "square", total_length * 4))
    return result

SAWS = get_saws()
SUPERB_SAWS = get_saws(a_ss=True) #, a_phase_smear=False)
SQUARES = get_squares()
TRIANGLES = get_squares(a_triangle=True)
SINES = get_sines()

RESULT = (
    (SAWS, "saw"), (SUPERB_SAWS, "superb_saw"),
    (SQUARES, "square"), (TRIANGLES, "triangle"),
    (SINES, "sine")
    )

for wavs, name in RESULT:
    dict_to_c_code(wavs, name)
    dict_to_wav(wavs, name)
    visualize(wavs)

