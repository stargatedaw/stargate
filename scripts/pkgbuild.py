#!/usr/bin/env python3
import argparse
import json
import os
import subprocess

from jinja2 import Template

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i',
        '--install',
        action='store_true',
        dest='install',
        help='Install the package after building',
    )
    return parser.parse_args()

ARGS = parse_args()

PKGBUILD = """\
pkgname={{ name }}
pkgver={{ version }}
pkgrel=1
pkgdesc="A DAW, plugins and wave editor"
arch=('i686' 'x86_64' 'aarch64')
url="https://github.com/stargatedaw/stargate"
license=('GPL')
groups=()
depends=(
    alsa-lib
    fftw
    lame
    libsndfile
    portaudio
    portmidi
    python
    python-jinja
    python-mutagen
    python-numpy
    python-psutil
    python-pyaml
    python-pyqt6
    qt6-svg
    rubberband
    vorbis-tools
)
makedepends=(
    alsa-lib
    fftw
    gcc
    libsndfile
    portaudio
    portmidi
    python
)
optdepends=()
provides=()
conflicts=()
replaces=()
backup=()
options=()
install=
changelog=
source=($pkgname-$pkgver.tar.gz)
noextract=()
md5sums=() #generate with 'makepkg -g'

prepare() {
  git submodule init
  git submodule update
}

build() {
  cd "$srcdir/$pkgname-$pkgver"
  PLAT_FLAGS="${CFLAGS}" make all
}

package() {
  cd "$srcdir/$pkgname-$pkgver"
  DESTDIR="$pkgdir/" make install
}

"""


orig_wd = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
    ),
)

os.chdir(orig_wd)
# Delete folders that the Arch package utils create, which cause the size of
# the tar files to grow
os.system('rm -rf src/stargate-[0-9][0-9].*')

with open("src/meta.json") as f:
    j = json.load(f)
    MAJOR_VERSION = j['version']['major']
    MINOR_VERSION = j['version']['minor']

t = Template(PKGBUILD)
output = t.render(
    name=MAJOR_VERSION,
    version=MINOR_VERSION,
)
with open('PKGBUILD', 'w') as f:
    f.write(output)

assert not os.system('scripts/src.sh')
assert not os.system('makepkg -g >>PKGBUILD')
assert not os.system('makepkg -fs')

if ARGS.install:
    assert not os.system(
        f'sudo pacman -U ./{MAJOR_VERSION}-{MINOR_VERSION}-*.zst',
    )
