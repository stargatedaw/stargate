#!/usr/bin/make -f

PREFIX ?= /usr
MAJOR := $(shell jq -r .version.major meta.json || echo stargate)
MINOR := $(shell jq -r .version.minor meta.json)
WMAJOR := $(shell /mingw64/bin/jq -r .version.major meta.json 2>/dev/null)
WMINOR := $(shell /mingw64/bin/jq -r .version.minor meta.json 2>/dev/null)
DESTDIR ?=
SG_DIR = $(DESTDIR)$(PREFIX)/share/$(MAJOR)
PIP ?= pip3
BROWSER ?= firefox

# --------------------------------------------------------------

all: sbsms commit_hash distro
	# General purpose build, including dependencies

clean: clean_pyc
	rm -rf htmlcov/ .pytest_cache/ .eggs/ .coverage \
		*.pyc *.egg-info build/ dist/
	make -C engine clean
	make -C vendor/sbsms clean

clean_pyc:
	find . -type d -name __pycache__ -exec rm -rf {} \; ; true

commit_hash:
	git rev-parse --short HEAD > COMMIT || echo unknown > COMMIT

deps_clean:
	make -C vendor/sbsms clean
	make -C vendor/sbsms/cli clean

distro: commit_hash
	# Build Stargate DAW without vendored dependencies, you are expected
	# to provide and package: mido, pymarshal, SBSMS, python-wavefile
	make -C engine

install: install_distro install_sbsms install_py_vendor
	# General purpose install for users

install_distro: clean_pyc
	# install without vendored dependencies
	install -d $(SG_DIR)
	install -d $(DESTDIR)$(PREFIX)/bin
	cp scripts/* $(DESTDIR)$(PREFIX)/bin
	install -d $(SG_DIR)/stargate
	install -m 755 engine/$(MAJOR)-engine-dbg $(DESTDIR)$(PREFIX)/bin
	install -s -m 755 engine/$(MAJOR)-engine $(DESTDIR)$(PREFIX)/bin
	cp -r sglib sgui $(SG_DIR)/stargate
	cp -r files/themes files/presets $(SG_DIR)
	cp -r files/themes files/plugin_assets files/fonts $(SG_DIR)
	cp -r files/share $(DESTDIR)/$(PREFIX)
	install -m 644 meta.json $(SG_DIR)
	install -m 644 COMMIT $(SG_DIR)

install_py_vendor:
	cp -r sg_py_vendor $(SG_DIR)/stargate

install_sbsms:
	install -m 755 \
		vendor/sbsms/cli/sbsms \
		$(DESTDIR)$(PREFIX)/bin/$(MAJOR)-sbsms

install_mac_osx:
	PREFIX=/usr/local make install

lines-of-code:
	./loc.sh

mac_osx: commit_hash
	cp -f \
		vendor/sbsms/cli/sbsms \
		/usr/local/bin/rubberband \
		engine/
	OPTIMIZE_FLAGS= CC=clang PREFIX=/usr/local make sbsms
	OPTIMIZE_FLAGS= CC=clang CC_ARGS= make -C engine mac_osx
	./macos/link.py

mingw:
	CFLAGS+=" -static-libgcc " make -C engine mingw

mingw_deps:
	# vendor/sbsms/cli/sbsms.exe
	cp \
		 /mingw64/bin/libFLAC-8.dll \
		 /mingw64/bin/libfftw3-3.dll \
		 /mingw64/bin/libfftw3f-3.dll \
		 /mingw64/bin/libgcc_s_seh-1.dll \
		 /mingw64/bin/libogg-0.dll \
		 /mingw64/bin/libopus-0.dll \
		 /mingw64/bin/libportaudio.dll \
		 /mingw64/bin/libportmidi.dll \
		 /mingw64/bin/librubberband-2.dll \
		 /mingw64/bin/libsamplerate-0.dll \
		 /mingw64/bin/libsndfile-1.dll \
		 /mingw64/bin/libssp-0.dll \
		 /mingw64/bin/libstdc++-6.dll \
		 /mingw64/bin/libwinpthread-1.dll \
		 /mingw64/bin/libvorbis-0.dll \
		 /mingw64/bin/libvorbisenc-2.dll \
		 /mingw64/bin/rubberband.exe \
		 engine/
	cp vendor/portaudio-binaries/libportaudio64bit.dll \
		engine/libportaudio.dll \
		|| echo "Could not install portaudio with ASIO support"

mingw_deps_clean:
	rm -rf engine/*.{dll,exe}

py_vendor:
	# Vendor pip dependencies
	mkdir -p ./sg_py_vendor
	$(PIP) install \
		--ignore-installed --upgrade --target=./sg_py_vendor pymarshal
	$(PIP) install \
		--ignore-installed --upgrade --target=./sg_py_vendor --no-deps wavefile

sbsms:
	cd vendor/sbsms && ( ./configure || ./configure --enable-sse=no ) && make
	cd vendor/sbsms/cli && make

tag_release:
	git tag release-$(MINOR)

tests:
	./test_parse.sh
	make -C engine test
	pytest test/
	$(BROWSER) htmlcov/index.html

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/$(MAJOR)*
	rm -rf $(SG_DIR)
	rm -rf $(DESTDOR)$(PREFIX)/share/*/stargate*

