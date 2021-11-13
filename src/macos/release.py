#!/usr/bin/env python3

import json
import os
import platform
import shutil
import subprocess

HOME = os.path.expanduser('~')

with open('meta.json') as f:
    j = json.load(f)
    MAJOR_VERSION = j['version']['major']
    MINOR_VERSION = j['version']['minor']

CWD = os.path.abspath(
        os.path.join(
        os.path.dirname(__file__),
        '..',
    ),
)
os.chdir(CWD)

subprocess.check_call([
    'make',
    'mac_osx',
])

BUNDLE = f'dist/{MAJOR_VERSION}.app'
if os.path.isdir(BUNDLE):
    shutil.rmtree(BUNDLE)

subprocess.check_call([
    f'{HOME}/Library/Python/3.8/bin/pyinstaller',
    f'--paths=(CWD)',
    'pyinstaller-mac-onedir.spec',
])

os.chdir('dist')
ARCH = platform.machine()

DMG = f'{MAJOR_VERSION}-{MINOR_VERSION}-macos-{ARCH}.dmg'
if os.path.exists(DMG):
    os.remove(DMG)

subprocess.check_call([
    'create-dmg',
    '--format', 'UDBZ',
    DMG,
    f'{MAJOR_VERSION}.app',
])

