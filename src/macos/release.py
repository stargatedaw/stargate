#!/usr/bin/env python3

import json
import os
import platform
import shutil
import subprocess

HOME = os.path.expanduser('~')
ARCH = platform.machine()

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

if ARCH == 'x86_64':
    subprocess.check_call([
        'make',
        'mac_osx',
    ])
elif ARCH == 'arm64':
    subprocess.check_call([
        'make',
        'mac_osx_arm',
    ])
else:
    assert False, f"Unknown arch. {ARCH}"

BUNDLE = f'dist/{MAJOR_VERSION}.app'
if os.path.isdir(BUNDLE):
    shutil.rmtree(BUNDLE)

for version in ('3.8', '3.9', '3.10', '3.11'):
    try:
        retcode = subprocess.check_call([
            f'{HOME}/Library/Python/{version}/bin/pyinstaller',
            f'--paths=(CWD)',
            '--noconfirm',
            'pyinstaller-mac-onedir.spec',
        ])
        break
    except:
        pass

assert retcode == 0, retcode

os.chdir('dist')

ARCH_NAMES = {
    'x86_64': 'intel',
    'arm64': 'm1',
}

DMG = f'{MAJOR_VERSION}-{MINOR_VERSION}-macos-{ARCH_NAMES[ARCH]}-{ARCH}.dmg'
if os.path.exists(DMG):
    os.remove(DMG)

subprocess.check_call([
    'create-dmg',
    '--format', 'UDBZ',
    DMG,
    f'{MAJOR_VERSION}.app',
])

