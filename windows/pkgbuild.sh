#!/bin/sh

MAJOR_VERSION=$(jq .version.major ../src/meta.json)

rm *.zip
wget https://github.com/stargataudio/stargate/archive/${MAJOR_VERSION}.zip
python3 pkgbuild.py
rm *.tar.xz *.exe *.zip
dos2unix PKGBUILD
makepkg-mingw -Cfs

echo "Now run nsis.py from outside of MSYS2 using Windows-native Python"

