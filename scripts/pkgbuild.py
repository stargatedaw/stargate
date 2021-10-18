#!/usr/bin/env python3
import json
import os

from jinja2 import Template


PKGBUILD = """\
pkgname={{ NAME }}
pkgver={{ VERSION }}
pkgrel=1
pkgdesc="A DAW, plugins and wave editor"
arch=('i686' 'x86_64')
url="https://stargateaudio.github.io"
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
    python-mido
    python-mutagen
    python-numpy
    python-psutil
    python-pyyaml
    python-pyqt6
    rubberband
    vorbis-tools
)
makedepends=(
    alsa-lib
    fftw
    gcc
    gcc-c++
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

build() {
  cd "$srcdir/$pkgname-$pkgver"

  make
}

package() {
  cd "$srcdir/$pkgname-$pkgver"

  make DESTDIR="$pkgdir/" install
}

"""


orig_wd = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
    ),
)

os.chdir(orig_wd)
os.system("scripts/src.sh")

with open("src/meta.json") as f:
    j = json.load(f)
    MAJOR_VERSION = j['version']['major']
    MINOR_VERSION = j['version']['minor']

t = Template(PKGBUILD)
output = t.render(
	name=MAJOR_VERSION,
	version=MINOR_VERSION,
)
with open('PKBUILD', 'w') as f:
	f.write(output)

os.system('makepkg')
