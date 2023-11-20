#!/usr/bin/env python3

import argparse
import copy
import os
import shutil
import subprocess
from glob import glob


CWD = os.path.abspath(
    os.path.dirname(__file__),
)
os.chdir(CWD)

def parse_args():
    parser = argparse.ArgumentParser('Create AppImages')
    parser.add_argument(
        '-p',
        '--python-version',
        default='3.11',
        dest='pyversion',
        help=(
            'The Python version to use, ie: 3.9, 3.8.  This should probably '
            'be set to the same version as is installed on the system, '
            'otherwise Python.h may be missing when building an AppImage'

        ),
    )
    return parser.parse_args()

def build(args):
    env = copy.deepcopy(os.environ)
    env['CURRENT_REPO'] = os.path.abspath(
        os.path.join(CWD, '..', '..'),
    )
    env['PT_EXCLUDE_LIBS'] = 'ALL'

    subprocess.check_call(
        [
            'python-appimage',
            'build',
            'app',
            '--python-version', args.pyversion,
            'stargate',
        ],
        env=env,
    )
    if not os.path.isdir('../../../dist'):
        os.mkdir('../../../dist')

    for appimage in glob('*.AppImage'):
        dest = os.path.join('..', '..', '..', 'dist', appimage)
        if os.path.exists(dest):
            print(f'Deleting old version {dest}')
            os.remove(dest)
        print(f'Moving {appimage} to ../../dist/')
        shutil.move(appimage, dest)

    print('Finished!  AppImage files are in ../dist/')

def main():
    args = parse_args()
    build(args)

if __name__ == '__main__':
    main()

