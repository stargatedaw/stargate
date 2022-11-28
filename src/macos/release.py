#!/usr/bin/env python3

import argparse
import json
import os
import platform
import shutil
import subprocess

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dmg',
        action='store_true',
        default=False,
        dest='dmg',
        help='Build a DMG installer instead of a PKG',
    )
    return parser.parse_args()

ARGS = parse_args()

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
        'macos',
    ])
elif ARCH == 'arm64':
    subprocess.check_call([
        'make',
        'macos_arm',
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

if ARGS.dmg:
    DMG = f'{MAJOR_VERSION}-{MINOR_VERSION}-macos-{ARCH_NAMES[ARCH]}-{ARCH}.dmg'
    if os.path.exists(DMG):
        os.remove(DMG)

    subprocess.check_call([
        'create-dmg',
        '--volname', f'{MAJOR_VERSION}',
        '--icon', f'{MAJOR_VERSION}.app', '50', '120',
        '--hide-extension', f'{MAJOR_VERSION}.app',
        '--app-drop-link', '300', '120',
        '--format', 'UDBZ',
        DMG,
        f'{MAJOR_VERSION}.app',
    ])
else:
    PKG = f'StargateDAW-{MINOR_VERSION}-macos-{ARCH_NAMES[ARCH]}-{ARCH}.pkg'
    subprocess.check_call([
        'pkgbuild',
        '--root', "stargate.app",
        '--identifier', 'com.github.stargatedaw.stargate',
        '--scripts', '../macos/Scripts',
        '--install-location', "/Applications/Stargate DAW.app",
        'Distribution.pkg',
    ])
    # Distribution.xml generated with:
    #   productbuild --synthesize --package Distribution.pkg Distribution.xml
    subprocess.check_call([
        'productbuild',
        '--distribution', '../macos/Distribution.xml',
        '--resources', 'Resources',
        '--package-path', '.',
        PKG,
    ])

