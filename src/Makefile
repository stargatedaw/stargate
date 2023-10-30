#!/usr/bin/make -f

PREFIX ?= /usr
MAJOR := $(shell jq -r .version.major meta.json || echo stargate)
MINOR := $(shell jq -r .version.minor meta.json)
WMAJOR := $(shell /mingw64/bin/jq -r .version.major meta.json 2>/dev/null)
WMINOR := $(shell /mingw64/bin/jq -r .version.minor meta.json 2>/dev/null)
DESTDIR ?=
SG_DIR ?= /opt/$(MAJOR)
SG_DEST = $(DESTDIR)/$(SG_DIR)
CC ?= /usr/bin/cc
CXX ?= /usr/bin/c++
PIP ?= pip3
BROWSER ?= firefox
DOCKER ?= podman
DOCKER_IMAGE ?= stargate-appimage-builder
MINGW_PREFIX ?= /mingw64
NUITKA_PYQT ?= pyqt5

# --------------------------------------------------------------

.PHONY: appimage

all: sbsms soundtouch distro
	# General purpose build, including dependencies

appimage:
	appimage/python-appimage/release.py
	$(DOCKER) run \
		--mount type=bind,src=..,dst=/stargate \
		$(DOCKER_IMAGE) \
		sh -c 'cd /stargate/src && ./appimage/appimage-helper.sh'
	appimagetool -n \
		../dist/squashfs-root/ \
		../dist/StargateDAW-$(MINOR)-linux-x86_64.AppImage

appimage-debug:
	appimage/python-appimage/release.py
	$(DOCKER) run -it \
		--mount type=bind,src=..,dst=/stargate \
		$(DOCKER_IMAGE) \
		sh

docker-image:
	$(DOCKER) build -t stargate-base  -f appimage/Dockerfile-base
	$(DOCKER) build -t $(DOCKER_IMAGE)  -f appimage/Dockerfile-appimage-builder

clean: clean_pyc
	rm -rf htmlcov/ .pytest_cache/ .eggs/ .coverage \
		*.pyc *.egg-info build/ dist/ vendor/stargate-soundstretch
	make -C engine clean
	make -C vendor/sbsms/cli clean

clean_pyc:
	find . -type d -name __pycache__ -exec rm -rf {} \; ; true

commit_hash:
	git rev-parse --short HEAD > COMMIT || echo unknown > COMMIT

distro: commit_hash
	# Build Stargate DAW without vendored dependencies, you are expected
	# to provide and package: mido, pymarshal, SBSMS, python-wavefile
	make -C engine

install: install_self_contained install_symlinks
	# General purpose install for users

install_self_contained:
	# Linux only, install all files to a single directory,
	# except for /usr/share desktop files and /usr/bin/stargate,
	# which should be symlinked by the package
	install -d $(SG_DEST)/engine
	install -m 755 engine/stargate-engine $(SG_DEST)/engine/
	install -m 755 vendor/sbsms/cli/sbsms* $(SG_DEST)/engine/
	install -m 755 vendor/stargate-soundstretch $(SG_DEST)/engine/
	cp -r files meta.json scripts sg_py_vendor sglib sgui $(SG_DEST)
	# install -d "$(DESTDIR)$(PREFIX)/share"
	# cp -r files/share/* "$(DESTDIR)$(PREFIX)/share/"

install_nuitka:
	cp -r stargate.dist $(SG_DEST)/stargate

install_symlinks: uninstall_symlinks
	# Symlink a self-contained install to the main system,
	# this requires root unless installing to an alternate DESTDIR or PREFIX
	install -d $(DESTDIR)$(PREFIX)/bin
	install -d $(DESTDIR)$(PREFIX)/share/applications
	install -d $(DESTDIR)$(PREFIX)/share/doc
	install -d $(DESTDIR)$(PREFIX)/share/mime/packages
	install -d $(DESTDIR)$(PREFIX)/share/pixmaps
	ln -rs $(DESTDIR)/opt/stargate/scripts/stargate \
		$(DESTDIR)$(PREFIX)/bin/stargate || true
	ln -rs $(DESTDIR)/opt/stargate/files/share/doc/stargate \
		$(DESTDIR)$(PREFIX)/share/doc/stargate || true
	ln -rs $(DESTDIR)/opt/stargate/files/share/pixmaps/stargate.png \
		$(DESTDIR)$(PREFIX)/share/pixmaps/stargate.png || true
	ln -rs $(DESTDIR)/opt/stargate/files/share/pixmaps/stargate.ico \
		$(DESTDIR)$(PREFIX)/share/pixmaps/stargate.ico || true
	ln -rs $(DESTDIR)/opt/stargate/files/share/applications/stargate.desktop \
		$(DESTDIR)$(PREFIX)/share/applications/stargate.desktop || true
	ln -rs $(DESTDIR)/opt/stargate/files/share/mime/packages/stargate.xml \
		$(DESTDIR)$(PREFIX)/share/mime/packages/stargate.xml || true

uninstall_symlinks:
	rm -rf $(DESTDIR)$(PREFIX)/share/doc/stargate
	rm -f \
		$(DESTDIR)$(PREFIX)/bin/stargate \
		$(DESTDIR)$(PREFIX)/share/pixmaps/stargate.png \
		$(DESTDIR)$(PREFIX)/share/pixmaps/stargate.ico \
		$(DESTDIR)$(PREFIX)/share/applications/stargate.desktop \
		$(DESTDIR)$(PREFIX)/share/mime/packages/stargate.xml

install_macos:
	PREFIX=/usr/local make install

lines-of-code:
	./loc.sh

macos: commit_hash soundtouch sbsms
	OPTIMIZE_FLAGS= CC=clang CC_ARGS= make -C engine macos
	cp -f \
		vendor/sbsms/cli/sbsms \
		vendor/stargate-soundstretch \
		/usr/local/bin/rubberband \
		engine/
	./macos/link.py

macos_arm: commit_hash soundtouch
	PLAT_FLAGS= CFLAGS+="-I/opt/homebrew/include" make sbsms
	make -C engine macos_arm
	# No idea why cp breaks this file, it makes no sense
	mv vendor/sbsms/cli/sbsms engine/
	cp -f \
		/opt/homebrew/bin/rubberband \
		vendor/stargate-soundstretch \
		engine/
	./macos/link.py

mingw:
	CFLAGS+=" -static-libgcc " make -C engine mingw

mingw_deps:
	CXX=$(MINGW_PREFIX)/bin/clang++ make -C vendor/sbsms/cli
	cp \
		$(MINGW_PREFIX)/bin/libFLAC.dll \
		$(MINGW_PREFIX)/bin/libfftw3-3.dll \
		$(MINGW_PREFIX)/bin/libfftw3f-3.dll \
		$(MINGW_PREFIX)/bin/libgcc_s_seh-1.dll \
		$(MINGW_PREFIX)/bin/libogg-0.dll \
		$(MINGW_PREFIX)/bin/libopus-0.dll \
		$(MINGW_PREFIX)/bin/libportaudio.dll \
		$(MINGW_PREFIX)/bin/libportmidi.dll \
		$(MINGW_PREFIX)/bin/librubberband-2.dll \
		$(MINGW_PREFIX)/bin/libsamplerate-0.dll \
		$(MINGW_PREFIX)/bin/libsndfile-1.dll \
		$(MINGW_PREFIX)/bin/libssp-0.dll \
		$(MINGW_PREFIX)/bin/libstdc++-6.dll \
		$(MINGW_PREFIX)/bin/libwinpthread-1.dll \
		$(MINGW_PREFIX)/bin/libvorbis-0.dll \
		$(MINGW_PREFIX)/bin/libvorbisenc-2.dll \
		$(MINGW_PREFIX)/bin/rubberband.exe \
		vendor/sbsms/cli/sbsms.exe \
		engine/
	cp vendor/portaudio-binaries/libportaudio64bit.dll \
		engine/libportaudio.dll \
		|| echo "Could not install portaudio with ASIO support"
	cd vendor/soundtouch && \
		$(MINGW_PREFIX)/bin/clang++ -Iinclude -lshlwapi -O3 \
			source/Sound{Stretch,Touch}/*.cpp \
			-o soundstretch.exe && \
		cp soundstretch.exe ../../engine/

mingw_deps_clean:
	rm -rf engine/*.{dll,exe}

nuitka-appimage:
	python3 -m nuitka \
		--standalone \
		--onefile \
		--linux-icon=files/share/pixmaps/stargate.png \
		--include-module=sgui \
		--include-module=sglib \
		--include-qt-plugins=platform,sensible \
		--enable-plugin=pyqt6 \
		--enable-plugin=pyqt5 \
		--include-data-dir=files=files \
		--include-data-files=engine/stargate-engine=engine/ \
		--include-data-files=meta.json=meta.json \
		--include-data-files=COMMIT=COMMIT \
		--include-data-files=vendor/sbsms/cli/sbsms=engine/ \
		--include-data-files=vendor/stargate-soundstretch=engine/ \
		scripts/stargate

nuitka-appbundle:
	python3 -m nuitka \
		--standalone \
		--include-module=sgui \
		--include-module=sglib \
		--include-qt-plugins=platform,sensible \
		--enable-plugin=pyqt6 \
		--include-data-dir=files=files \
		--include-data-files=engine/stargate-engine=engine/ \
		--include-data-files=engine/*.dylib=engine/ \
		--include-data-files=engine/sbsms=engine/ \
		--include-data-files=meta.json=meta.json \
		--include-data-files=COMMIT=COMMIT \
		--include-data-files=engine/sbsms=engine/ \
		--include-data-files=engine/rubberband=engine/ \
		--include-data-files=engine/stargate-soundstretch=engine/ \
		--macos-target-arch=arm64 \
		--macos-create-app-bundle \
		--macos-app-icon=macos/stargate.icns \
		--macos-app-name='Stargate DAW' \
		--macos-signed-app-name=com.github.stargatedaw.stargate \
		--macos-app-mode=gui \
		--macos-app-version=$(MINOR) \
		scripts/stargate
	mkdir -p dist
	rm -rf dist/stargate.app/
	mv stargate.app 'dist/Stargate DAW.app'

py_vendor:
	# Vendor Python dependencies not commonly available in distro repos
	mkdir -p ./sg_py_vendor
	$(PIP) install \
		--ignore-installed --upgrade --target=./sg_py_vendor pymarshal
	$(PIP) install \
		--ignore-installed --upgrade --target=./sg_py_vendor --no-deps wavefile
	$(PIP) install \
		--ignore-installed --upgrade --target=./sg_py_vendor mido

sbsms:
	make -C vendor/sbsms/cli

soundtouch:
	cd vendor/soundtouch && \
		$(CXX) -std=c++11 -Iinclude/ -O3 \
		`find source/SoundTouch source/SoundStretch -name '*.cpp'` \
		-o ../stargate-soundstretch

tag_release:
	git tag release-$(MINOR)

tests:
	./test_parse.sh
	make -C engine test
	pytest test/
	$(BROWSER) htmlcov/index.html

uninstall: uinstall_symlinks
	rm -rf $(SG_DEST)
