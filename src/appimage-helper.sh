#!/bin/sh -xe

cd /stargate
VERSION=$(jq .version.minor meta.json)

cd dist/
rm -rf squashfs-root
./stargate-x86_64.AppImage --appimage-extract
cd ..
DESTDIR=dist/squashfs-root PREFIX=/usr make \
	install_dirs \
	install_engine \
	install_sbsms

DESTDIR=dist/squashfs-root PREFIX=/opt/python3.10 make \
	install_dirs \
	install_files

export DESTDIR=/stargate/dist/squashfs-root
export PREFIX=/usr
cd /root/libsndfile-1.1.0/
make install
cd /root/portaudio-19.7.0/
make install
cd /root/portmidi-2.0.4/
make install

PACKAGES=$(apt-cache depends --recurse --no-recommends --no-suggests \
--no-conflicts --no-breaks --no-replaces --no-enhances \
	libfftw3-3 \
	rubberband-cli \
	libflac8 \
	libogg0 \
	libmp3lame0 \
	libmpg123-0 \
	libopus0 \
	libvorbis0a \
	vorbis-tools \
| grep "^\w" | grep -vE 'gcc|libc|libstdc|perl' | sort -u)

cd /stargate/dist
mkdir -p packages/
cd packages/
apt-get download ${PACKAGES}
cd ..

mkdir -p squashfs-root/var/lib/
ln -s /var/lib/dpkg squashfs-root/var/lib/dpkg
# This always fails some packages, but it still works
dpkg -i --log=filename --root=squashfs-root/ packages/* || true


#appimagetool -n \
#	squashfs-root/ \
#	StargateDAW-${VERSION}-linux-x86_64.AppImage

