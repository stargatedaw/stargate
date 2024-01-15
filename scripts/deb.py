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
        help="Install the package after creating it",
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
    "libportmidi-dev",
    "libsndfile1-dev",
    "libtool",
    "portaudio19-dev",
    "python3-dev",
    "python3-pip",
])

depends = [
    "fftw3 | libfftw3-single3",
    "libasound2",
    "libportaudio2",
    "libportmidi0",
    "libsndfile1",
    "python3",
    "python3-jinja2",
    "python3-mido",
    "python3-mutagen",
    "python3-numpy",
    "python3-psutil",
    "python3-pyqt6 | python3-pyqt5",
    "python3-pyqt6.qtsvg | python3-pyqt5.qtsvg",
    "python3-yaml",
    "rubberband-cli",
    "vorbis-tools",
]

recommends = ", ".join([
    "ffmpeg",
    "lame",
])

if arch.lower().startswith("arm"):
    # Used to detect if a Raspberry Pi is running a sufficiently lightweight
    # desktop to be able to render the UI
    depends.append("wmctrl")
    depends.sort()
depends = ", ".join(depends)

CONTROL_FILE = f"""\
Package: stargate
Version: {minor_version}
Architecture: {arch}
Maintainer: stargateaudio@noreply.github.com
Description: A holistic audio production solution.
  Stargate is a DAW, instruments, effects and a wave editor.
  Everything you need to create music on a computer.
Build-Depends: {build_depends}
Depends: {depends}
Recommends: {recommends}
"""

postinst = """\
#!/bin/sh

# Create file association for stargate.project
# update-mime-database /usr/share/mime/  || true
# xdg-mime default stargate.desktop text/stargate.project || true
"""

if args.plat_flags is None:
    assert not os.system("make")
else:
    assert not os.system(f"PLAT_FLAGS='{args.plat_flags}' make")
assert not os.system(f"DESTDIR='{root}' make install")
assert not os.system(f"find '{root}' -name '*.pyc' -delete")
DEBIAN = os.path.join(root, 'DEBIAN')
os.makedirs(DEBIAN)
control = os.path.join(DEBIAN, 'control')
with open(control, 'w') as f:
    f.write(CONTROL_FILE)
postinst_path = os.path.join(
    DEBIAN,
    'postinst',
)
with open(postinst_path, 'w') as f:
    f.write(postinst)
os.chmod(postinst_path, 0o755)

package = f"{major_version}-{minor_version}-{arch}.deb"
retcode = os.system(f"dpkg-deb --build --root-owner-group {root} {package}")
assert not retcode, retcode

package_path = os.path.join(CWD, package)
print(f"Created {package_path}")

if args.install:
    retcode = os.system(f'sudo apt install -y --reinstall ./{package}')

exit(retcode)
