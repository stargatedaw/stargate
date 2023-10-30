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
        '--pkg',
        action='store_true',
        default=False,
        dest='pkg',
        help='Build a PKG installer instead of a DMG',
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

BUNDLE = 'Stargate DAW.app'
BUNDLE_PATH = os.path.join('dist', BUNDLE)
if os.path.isdir(BUNDLE_PATH):
    shutil.rmtree(BUNDLE_PATH)

if ARCH == 'x86_64':
    retcode = subprocess.check_call([
        'pyinstaller',
        '--noconfirm',
        'pyinstaller-mac-onedir.spec',
    ])
elif ARCH == 'arm64':
    retcode = subprocess.check_call([
        'make',
        'nuitka-appbundle',
    ])
else:
    assert False, f"Unknown arch. {ARCH}"
assert retcode == 0, retcode

os.chdir('dist')

ARCH_NAMES = {
    'x86_64': 'intel',
    'arm64': 'm1',
}

def build_dmg():
    DMG = f'StargateDAW-{MINOR_VERSION}-macos-{ARCH_NAMES[ARCH]}-{ARCH}.dmg'
    if os.path.exists(DMG):
        os.remove(DMG)

    subprocess.check_call([
        'create-dmg',
        '--volname', 'Stargate DAW',
        '--icon', BUNDLE, '50', '120',
        '--hide-extension', BUNDLE,
        '--app-drop-link', '300', '120',
        '--format', 'UDBZ',
        DMG,
        BUNDLE,
    ])

def build_pkg():
    PKG = f'StargateDAW-{MINOR_VERSION}-macos-{ARCH_NAMES[ARCH]}-{ARCH}.pkg'
    subprocess.check_call([
        'pkgbuild',
        '--root', BUNDLE,
        '--identifier', 'com.github.stargatedaw.stargate',
        '--scripts', '../macos/Scripts',
        '--install-location', f"/Applications/{BUNDLE}",
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

if ARGS.pkg:
    build_pkg()
else:
    build_dmg()

