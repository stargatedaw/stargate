#!/usr/bin/make -f

PREFIX ?= /usr
VERSION := $(shell jq -r .version.major meta.json || echo stargate)
DESTDIR ?=
SBSMS_PREFIX = $(PREFIX)/lib/$(VERSION)/sbsms
SG_DIR = $(DESTDIR)$(PREFIX)/lib/$(VERSION)
PIP ?= pip3
BROWSER ?= firefox-wayland

# --------------------------------------------------------------

all: deps py_vendor
	make -C engine

clean: clean_pyc
	rm -rf htmlcov/ .pytest_cache/ .eggs/ .coverage \
		*.pyc *.egg-info build/ dist/
	make -C engine clean
	make -C vendor/sbsms clean

clean_pyc:
	find . -type d -name __pycache__ -exec rm -rf {} \; ; true

deps:
	cd vendor/sbsms && ( ./configure || ./configure --enable-sse=no ) && make
	cd vendor/sbsms/cli && make

deps_clean:
	make -C vendor/sbsms clean
	make -C vendor/sbsms/cli clean

install: clean_pyc
	install -d $(SG_DIR)
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 \
		vendor/sbsms/cli/sbsms \
		$(DESTDIR)$(PREFIX)/bin/$(VERSION)-sbsms
	cp scripts/* $(DESTDIR)$(PREFIX)/bin
	install -d $(SG_DIR)/stargate
	install -m 755 engine/$(VERSION)-engine-dbg $(DESTDIR)$(PREFIX)/bin
	install -s -m 4755 engine/$(VERSION)-engine $(DESTDIR)$(PREFIX)/bin
	cp -r sg_py_vendor sglib sgui $(SG_DIR)/stargate
	cp -r files/themes files/presets $(SG_DIR)
	cp -r files/share $(DESTDIR)/$(PREFIX)
	install -m 644 meta.json $(SG_DIR)

lines-of-code:
	./loc.sh

mac_osx:
	OPTIMIZE_FLAGS= CC=clang PREFIX=/usr/local make deps
	OPTIMIZE_FLAGS= CC=clang make -C engine mac_osx

mingw:
	CFLAGS+=" -static-libgcc " make -C engine mingw

mingw_deps:
	cp \
		 /mingw64/bin/libFLAC-8.dll \
		 /mingw64/bin/libfftw3f-3.dll \
		 /mingw64/bin/libogg-0.dll \
		 /mingw64/bin/libopus-0.dll \
		 /mingw64/bin/libportaudio-2.dll \
		 /mingw64/bin/libportmidi.dll \
		 /mingw64/bin/librubberband-2.dll \
		 /mingw64/bin/libsndfile-1.dll \
		 /mingw64/bin/libssp-0.dll \
		 /mingw64/bin/libwinpthread-1.dll \
		 /mingw64/bin/libvorbis-0.dll \
		 /mingw64/bin/libvorbisenc-2.dll \
		 /mingw64/bin/rubberband.exe \
		 engine/

mingw_deps_clean:
	rm -rf scripts/*.{dll,exe}

py_vendor:
	mkdir -p ./sg_py_vendor
	$(PIP) install \
		--ignore-installed --target=./sg_py_vendor pymarshal
	$(PIP) install \
		--ignore-installed --target=./sg_py_vendor --no-deps wavefile

tests:
	./test_parse.sh
	make -C engine test
	pytest test/
	$(BROWSER) htmlcov/index.html

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/$(VERSION)*
	rm -rf $(SG_DIR)
	rm -rf $(DESTDOR)$(PREFIX)/share/*/stargate*

