#!/usr/bin/python3
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

import argparse
import json
import os
import sys

os.chdir(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        'src',
    ),
)

with open("meta.json") as f:
    MK_VERSION = json.load(f)['version']['major']

BIN = "./engine/{}-engine".format(MK_VERSION)
HOME = os.path.expanduser("~")
LAST_PROJECT = os.path.join(HOME, MK_VERSION, "config", "last-project.txt")

if os.path.exists(LAST_PROJECT):
    with open(LAST_PROJECT) as f_file:
        PROJECT = os.path.dirname(f_file.read().strip())
else:
    PROJECT = os.path.join(HOME, MK_VERSION, "default-project")

TOOLS = {
    "benchmark": "make clean > /dev/null 2>&1 && "
        "make release > /dev/null 2>&1 && "
        "{BIN} {HOST} '{PROJECT}' test.wav {TIME} {SR} 512 {CORES} 1 0 "
        "--no-file",
    "valgrind": "make clean > /dev/null 2>&1 && "
        "make dbg > /dev/null 2>&1 && "
        "valgrind --alignment=16 --track-origins=yes "
        "{BIN}-dbg {HOST} '{PROJECT}' test.wav {TIME} {SR} 512 {CORES} 0 0 "
        "--no-file",
    "perf": "make clean > /dev/null 2>&1 && "
        "make release > /dev/null 2>&1 && "
        "perf stat -e cache-references,cache-misses,dTLB-loads,"
        "dTLB-load-misses,iTLB-loads,iTLB-load-misses,L1-dcache-loads,"
        "L1-dcache-load-misses,L1-icache-loads,L1-icache-load-misses,"
        "branch-misses,LLC-loads,LLC-load-misses "
        "{BIN} {HOST} '{PROJECT}' test.wav {TIME} {SR} 512 {CORES} 1 0 "
        "--no-file",
    "profile": "make clean && make gprof && "
        "{BIN} {HOST} '{PROJECT}' test.wav {TIME} {SR} 512 {CORES} 1 0 "
        "&& gprof {BIN} > profile.txt && gedit profile.txt",
    "pahole": "make clean && make dbg && pahole {BIN}",
    "gdb": "make dbg > /dev/null 2>&1 && "
        "echo run {HOST} '{PROJECT}' test.wav {TIME} {SR} 512 {CORES} 1 0 "
        "--no-file && gdb {BIN}-dbg ",
}

parser = argparse.ArgumentParser(
    description="Diagnostic tool for Stargate",
)
parser.add_argument(
    'tool',
    choices=sorted(TOOLS),
    help="The tool to use",
)
parser.add_argument(
    '--cores',
    default=1,
    help="The number of cores to use",
    type=int,
)
parser.add_argument(
    '--sample-rate',
    default=44100,
    dest='sr',
    help="The sample rate to use",
    type=int,
)
args = parser.parse_args()
TIME = "0 96"

CMD = TOOLS[args.tool].format(
    BIN=BIN,
    CORES=args.cores,
    HOST="dawnext",
    PROJECT=PROJECT,
    SR=args.sr,
    TIME=TIME,
)
print("Command:")
print(CMD)
print()
result = os.system(CMD)

if result:
    print("Returned exit code {}".format(result))

