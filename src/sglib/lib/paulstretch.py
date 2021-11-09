#!/usr/bin/env python3
#
# Paul's Extreme Sound Stretch (Paulstretch) - Python version
# originally by Nasca Octavian PAUL, Targu Mures, Romania
#
# Forked to allow better integration with Stargate
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

from argparse import ArgumentParser
import numpy
import os
import subprocess
import sys

f_parent_dir = os.path.dirname(os.path.abspath(__file__))
f_parent_dir = os.path.abspath(os.path.join(f_parent_dir, ".."))
lib_dir = os.path.abspath(
    os.path.join(
        f_parent_dir,
        'share',
        'stargate',
        'stargate',
    ),
)
sys.path.insert(0, f_parent_dir)
sys.path.insert(0, lib_dir)
print(f_parent_dir)
print(lib_dir)

from sglib.log import LOG
from sglib.lib.util import *
from sglib.lib._ctypes import *
os.environ['LIBRARY_PATH'] = ENGINE_DIR
LOG.info(ENGINE_DIR)
patch_ctypes()

try:
    from sg_py_vendor import wavefile
except ImportError:
    import wavefile

revert_patch_ctypes()


def optimize_windowsize(n):
    orig_n = n
    while True:
        n=orig_n
        while (n % 2) == 0:
            n /= 2
        while (n % 3) == 0:
            n /= 3
        while (n % 5) == 0:
            n /= 5
        if n < 2:
            break
        orig_n += 1
    return orig_n


def paulstretch(
    file_path,
    stretch,
    windowsize_seconds,
    onset_level,
    outfilename,
):
    stretch = numpy.double(stretch)
    windowsize_seconds = numpy.double(windowsize_seconds)
    onset_level = numpy.double(onset_level)

    if not os.path.exists(file_path):
        LOG.info("Error: {} does not exist.".format(file_path))
        return

    f_reader = wavefile.WaveReader(file_path)
    samplerate = f_reader.samplerate
    nsamples = f_reader.frames

    # Set max window size to 1/8th the size of the sample
    max_window_size = (float(nsamples) / float(samplerate)) * 0.125

    if windowsize_seconds > max_window_size:
        windowsize_seconds = max_window_size

    nchannels = f_reader.channels

    outfile = wavefile.WaveWriter(
        outfilename,
        channels=nchannels,
        samplerate=samplerate,
    )

    #make sure that windowsize is even and larger than 16
    windowsize = int(windowsize_seconds * samplerate)
    if windowsize < 16:
        windowsize = 16
    windowsize = optimize_windowsize(windowsize)
    windowsize = int(windowsize / 2) * 2
    half_windowsize = int(windowsize / 2)

    smp = numpy.zeros((nchannels, nsamples), numpy.float32, order='F')
    f_reader.read(smp)

    #correct the end of the smp

    end_size = int(samplerate * 0.05)
    if end_size < 16:
        end_size = 16

    smp[:,nsamples-end_size:nsamples] *= numpy.linspace(1.0, 0.0, end_size)

    #compute the displacement inside the input file
    start_pos = 0.0
    displace_pos = windowsize * 0.5

    #create Hann window
    window = 0.5 - numpy.cos(numpy.arange(windowsize, dtype='double') * \
        2.0 * numpy.pi / (windowsize - 1)) * 0.5

    old_windowed_buf = numpy.zeros((nchannels, windowsize))
    hinv_sqrt2 = (1 + numpy.sqrt(0.5)) * 0.5
    hinv_buf = (
        2.0 * (
            hinv_sqrt2 - (1.0 - hinv_sqrt2) * numpy.cos(numpy.arange(
                half_windowsize,
                dtype='double',
            ) * 2.0 * numpy.pi / half_windowsize)
        ) / hinv_sqrt2
    )

    freqs = numpy.zeros((nchannels, half_windowsize + 1))
    old_freqs = freqs

    num_bins_scaled_freq = 32
    freqs_scaled = numpy.zeros(num_bins_scaled_freq)
    old_freqs_scaled = freqs_scaled

    displace_tick = 0.0
    displace_tick_increase = 1.0 / stretch
    if displace_tick_increase > 1.0:
        displace_tick_increase = 1.0
    extra_onset_time_credit = 0.0
    get_next_buf = True

    while True:
        if get_next_buf:
            old_freqs = freqs
            old_freqs_scaled = freqs_scaled

            #get the windowed buffer
            istart_pos = int(numpy.floor(start_pos))
            buf = smp[:,istart_pos:istart_pos + windowsize]
            if buf.shape[1] < windowsize:
                buf = numpy.append(
                    buf,
                    numpy.zeros((nchannels, windowsize - buf.shape[1])),
                    1,
                )
            buf = buf * window

            # get the amplitudes of the frequency components
            # and discard the phases
            freqs = numpy.abs(numpy.fft.rfft(buf))

            #scale down the spectrum to detect onsets
            freqs_len = freqs.shape[1]
            if num_bins_scaled_freq < freqs_len:
                freqs_len_div = freqs_len // num_bins_scaled_freq
                new_freqs_len = freqs_len_div * num_bins_scaled_freq
                freqs_scaled = numpy.mean(
                    numpy.mean(freqs, 0)[:new_freqs_len].reshape(
                    [num_bins_scaled_freq, freqs_len_div]), 1)
            else:
                freqs_scaled = numpy.zeros(num_bins_scaled_freq)

            #process onsets
            m = 2.0 * numpy.mean(
                freqs_scaled - old_freqs_scaled
            ) / (numpy.mean(numpy.abs(old_freqs_scaled)) + 1e-3)
            if m < 0.0:
                m = 0.0
            if m > 1.0:
                m = 1.0

            if m > onset_level:
                displace_tick = 1.0
                extra_onset_time_credit += 1.0

        cfreqs = (freqs * displace_tick) + (old_freqs * (1.0 - displace_tick))

        # randomize the phases by multiplication with a random
        # complex number with modulus=1
        ph = numpy.random.random(
            size=(nchannels, cfreqs.shape[1])
        ) * (2. * numpy.pi) * 1j
        cfreqs = cfreqs * numpy.exp(ph)

        #do the inverse FFT
        buf = numpy.fft.irfft(cfreqs)

        #window again the output buffer
        buf *= window

        #overlap-add the output
        output = buf[:,0:half_windowsize] + \
            old_windowed_buf[:,half_windowsize:windowsize]
        old_windowed_buf=buf

        #remove the resulted amplitude modulation
        output *= hinv_buf

        outfile.write(output)

        if get_next_buf:
            start_pos += displace_pos

        get_next_buf = False

        if start_pos >= nsamples:
            break

        if extra_onset_time_credit <= 0.0:
            displace_tick += displace_tick_increase
        else:
            #this must be less than displace_tick_increase
            credit_get = 0.5 * displace_tick_increase
            extra_onset_time_credit -= credit_get
            if extra_onset_time_credit < 0:
                extra_onset_time_credit = 0
            displace_tick += displace_tick_increase - credit_get

        if displace_tick >= 1.0:
            displace_tick = displace_tick % 1.0
            get_next_buf = True

    outfile.close()


def main():
    print("Paul's Extreme Sound Stretch (Paulstretch) - Python version 20110223")
    print("new method: using onsets information")
    print("by Nasca Octavian PAUL, Targu Mures, Romania\n")
    parser = ArgumentParser(
        description="CLI for Paulstretch"
    )
    parser.add_argument(
      'input',
      help='Path to the input file',
    )
    parser.add_argument(
      'output',
      help='Path to the output file',
    )
    parser.add_argument(
        "--stretch",
        "-s",
        default=8.0,
        dest="stretch",
        help="stretch amount (1.0 = no stretch)",
        type=float,
    )
    parser.add_argument(
        "--window_size",
        "-w",
        default=0.25,
        dest="window_size",
        help="window size (seconds)",
        type=float,
    )
    parser.add_argument(
        "--onset",
        "-t",
        default=10.0,
        dest="onset",
        help="onset sensitivity (0.0=max, 1.0=min)",
        type=float,
    )
    parser.add_argument(
        "--start-pitch",
        "-p",
        default=None,
        dest="start_pitch",
        help="start pitch (36.0=max, -36.0=min)",
        type=float,
    )
    parser.add_argument(
        "--end-pitch",
        "-e",
        default=None,
        dest="end_pitch",
        help="end pitch (36.0=max, -36.0=min)",
        type=float,
    )

    args = parser.parse_args()

    if (
        args.stretch <= 0.0
        or
        args.window_size <= 0.001
    ):
        print("Error in command line parameters. Run this program with "
            "--help for help.")
        sys.exit(1)

    print("stretch amount = {}".format(args.stretch))
    print("window size = {} seconds".format(args.window_size))
    print("onset sensitivity = {}".format(args.onset))

    paulstretch(
        args.input,
        numpy.double(args.stretch),
        numpy.double(args.window_size),
        numpy.double(args.onset),
        args.output,
        args.start_pitch,
        args.end_pitch,
        args.input,
    )

if __name__ == "__main__":
    main()

