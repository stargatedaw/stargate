#!/usr/bin/env python3
"""
    Script for creating Debian packages
"""

import argparse
import json
import os
import shutil
import subprocess
import tempfile

def parse_args():
    parser = argparse.ArgumentParser(
        description="Debian package creator script",
    )
    parser.add_argument(
        '-i',
        '--install',
        action='store_true',
        dest='install',
        help="Install the pacakge after creating it",
    )
    parser.add_argument(
        '--plat-flags',
        dest='plat_flags',
        default=None,
        help='Use non-default PLAT_FLAGS to compile',
    )
    return parser.parse_args()

args = parse_args()
if args.install:
    # Warm up sudo
    assert not os.system('sudo echo')

CWD = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        'src',
    ),
)
os.chdir(CWD)
root = './tmp'
if os.path.isdir(root):
    shutil.rmtree(root)
os.makedirs(root)

with open('meta.json') as f:
    j = json.load(f)
major_version = j['version']['major']
minor_version = j['version']['minor']

arch = subprocess.check_output(['dpkg-architecture', '-q', 'DEB_HOST_ARCH'])
arch = arch.strip()
arch = arch.decode('UTF-8')

build_depends = ", ".join([
    "autoconf",
    "automake",
    "build-essential",
    "cython3",
    "debhelper",
    "dh-make",
    "g++",
    "gcc",
    "gdb",
    "gettext",
    "libasound2-dev",
    "libfftw3-dev",
    "liblo-dev",
    "libportmidi-dev",
    "libsndfile1-dev",
    "libtool",
    "portaudio19-dev",
    "python3-dev",
    "python3-pip",
])

depends = ", ".join([
    "ffmpeg",
    "fftw3",
    "lame",
    "libasound2",
    "liblo7",
    "libportaudio2",
    "libportmidi0",
    #"libsbsms10",
    "libsndfile1",
    "python3",
    "python3-jinja2",
    "python3-liblo",
    "python3-mido",
    "python3-mutagen",
    "python3-numpy",
    "python3-psutil",
    "python3-pyqt5",
    "rubberband-cli",
    "vorbis-tools",
])

CONTROL_FILE = f"""\
Package: stargate
Version: {minor_version}
Architecture: {arch}
Maintainer: stargateaudio@noreply.github.com
Description: A holistic audio production solution.
  Stargate is DAW, instruments, effects and a wave editor.  Everything you
  need to create music.
Build-Depends: {build_depends}
Depends: {depends}
"""

if args.plat_flags is None:
    assert not os.system("make")
else:
    assert not os.system(f"PLAT_FLAGS='{args.plat_flags}' make")
assert not os.system(f"DESTDIR={root} make install")
DEBIAN = os.path.join(root, 'DEBIAN')
os.makedirs(DEBIAN)
control = os.path.join(DEBIAN, 'control')
with open(control, 'w') as f:
    f.write(CONTROL_FILE)
retcode = os.system(f"dpkg-deb --build --root-owner-group {root}")
assert not retcode, retcode
package = f"{major_version}-{minor_version}-{arch}.deb"
os.rename(
    "tmp.deb",
    package,
)
package_path = os.path.join(CWD, package)
print(f"Created {package_path}")

if args.install:
    retcode = os.system(f'sudo apt install -y --reinstall ./{package}')

exit(retcode)
