#!/usr/bin/env python3
import hashlib
import os

PKGBUILD_TEMPLATE = """\
# Maintainer: stargateaudio <stargateaudio@noreply.github.com>

_realname={major_version}
pkgname="${{MINGW_PACKAGE_PREFIX}}-${{_realname}}"
pkgver={minor_version}
pkgrel=1
pkgdesc="DAWs/hosts, instrument and effect plugins, and a new approach to audio development. (mingw-w64)"
arch=('any')
url="http://www.github.com/stargateaudio/stargate"
license=("GPL")
makedepends=("${{MINGW_PACKAGE_PREFIX}}-gcc" "${{MINGW_PACKAGE_PREFIX}}-pkg-config")
depends=("${{MINGW_PACKAGE_PREFIX}}-gcc-libs"
         "${{MINGW_PACKAGE_PREFIX}}-rubberband"
         "${{MINGW_PACKAGE_PREFIX}}-portaudio"
         "${{MINGW_PACKAGE_PREFIX}}-portmidi"
         "${{MINGW_PACKAGE_PREFIX}}-libsndfile"
         "${{MINGW_PACKAGE_PREFIX}}-fftw"
         "${{MINGW_PACKAGE_PREFIX}}-python3-numpy"
         "${{MINGW_PACKAGE_PREFIX}}-libvorbis"
         "${{MINGW_PACKAGE_PREFIX}}-python3-pyqt5")
source=("https://github.com/stargateaudio/stargate/archive/{major_version}.zip")
md5sums=('{zip_md5sum}')

build() {{
  #export PATH="${{MINGW_PREFIX}}:$PATH"
  cd "${{srcdir}}/stargate-{major_version}/src"
  CC=${{MINGW_PREFIX}}/bin/gcc.exe make mingw
}}

package() {{
  #export PATH="${{MINGW_PREFIX}}:$PATH"
  cd "${{srcdir}}/stargate-{major_version}/src"
  make PREFIX=${{MINGW_PREFIX}} DESTDIR="$pkgdir" install_non_linux
}}

"""

CWD = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(CWD, "..", "src", "meta.json")) as f:
    j = json.load(f)
    MINOR_VERSION = j['version']['minor']
    MAJOR_VERSION = j['version']['major']

file_name = os.path.join(
    CWD,
    "{major_version}.zip".format(
        major_version=MAJOR_VERSION,
    ),
)

with open(file_name, "rb") as fh:
    MD5_ZIP = hashlib.md5(fh.read()).hexdigest()

PKGBUILD = os.path.join(CWD, "PKGBUILD")

with open(PKGBUILD, "w") as fh:
    tmp_str = PKGBUILD_TEMPLATE.format(
        major_version=MAJOR_VERSION, minor_version=MINOR_VERSION,
        zip_md5sum=MD5_ZIP)
    fh.write(tmp_str)

