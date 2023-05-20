#!/usr/bin/env python3

import argparse
import collections
import copy
import glob
import os
import shutil
import subprocess

def parse_args():
    parser = argparse.ArgumentParser()
    return parser.parse_args()

args = parse_args()

CWD = os.path.abspath(
        os.path.join(
        os.path.dirname(__file__),
        '..',
        'engine',
    ),
)
os.chdir(CWD)

def relink(binary):
    otool = subprocess.check_output([
        'otool',
        '-L',
        binary,
    ]).decode('utf-8')
    for line in otool.split('\n'):
        arr = line.split()
        if not arr:
            continue
        dylib = arr[0]
        if (
            (
                dylib.startswith('/usr/local/') 
                or
                dylib.startswith('/opt/homebrew/') 
            ) and 
            dylib.endswith('.dylib')
        ):
            basename = os.path.basename(dylib)
            print(
                f'Relinking {binary} -> {basename}',
            )
            subprocess.check_output([
                'install_name_tool',
                '-change',
                dylib,
                f'@loader_path/{basename}',
                binary,
            ])

            if not os.path.exists(basename):
                shutil.copyfile(dylib, basename)
                relink(basename)

BINARIES = ['stargate-engine', 'rubberband', 'sbsms']

for binary in BINARIES:
    relink(binary)

