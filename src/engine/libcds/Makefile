#!/usr/bin/make -f

NAME ?= libcds

# Compiler flags
CC ?= gcc
CC_ARGS ?= -Wall -fPIC
OPT_LVL ?= -O2
# These assume a modern x86 CPU, change or remove for other platforms
PLAT_FLAGS ?= -mfpmath=sse -mssse3
# Remove -ggdb3 to use with other debuggers like lldb
DEBUG_FLAGS ?= -g -ggdb3

# Used only for RPM packaging
ARCH ?= $(shell uname --machine)

# Arguments required to generate gcov coverage report
GCOVARGS ?= -fprofile-arcs -ftest-coverage  # -fPIC

# Coverage reports will be viewed in this browser
BROWSER ?= firefox-wayland

# Install, packaging arguments
DESTDIR ?=
LIBDIR ?= /usr/lib
INCLUDEDIR ?= /usr/include

# benchmark inputs
# Tells benchmarks that use the ITERATIONS macro how many iterations to attempt
BENCH_ITERATIONS ?= 100000000UL
# Tells the benchmarks to try not using more than this amount of memory.  It
# is not guaranteed that this number will not be exceeded
BENCH_SIZE_MB ?= 500UL

# Kernel and hardware performance counters for `make perf`
# See `perf list` for all available counters
PERF_COUNTERS ?= "cache-references,cache-misses,dTLB-loads,\
dTLB-load-misses,iTLB-loads,iTLB-load-misses,L1-dcache-loads,\
L1-dcache-load-misses,L1-icache-loads,L1-icache-load-misses,\
branch-misses,LLC-loads,LLC-load-misses"


all: shared

bench:
	# Run the benchmark, output the results as YAML to stderr
	$(CC) \
	    $(CC_ARGS) $(OPT_LVL) $(PLAT_FLAGS) \
	    $(shell find src benchmark -name *.c) -Iinclude \
	    -DITERATIONS=$(BENCH_ITERATIONS) \
	    -DBENCH_SIZE_MB=$(BENCH_SIZE_MB) \
	    -o $(NAME).benchmark
	./$(NAME).benchmark

bench-test:
	# Run the benchmark through valgrind and gcov
	$(CC) \
	    $(CC_ARGS) -O0 $(DEBUG_FLAGS) $(PLAT_FLAGS) $(GCOVARGS) \
	    $(shell find src benchmark -name *.c) -Iinclude \
	    -DITERATIONS=100 -DBENCH_SIZE_MB=1 \
	    -o $(NAME).benchmark
	# If Valgrind exits non-zero, try running 'gdb ./ctemplate.tests'
	# to debug the test suite
	valgrind ./$(NAME).benchmark --track-origins=yes
	mkdir html || rm -rf html/*
	gcovr -r . --html --html-details \
		--exclude=tests \
		-o html/coverage.html
	$(BROWSER) html/coverage.html &
	# NOTE: You do not need to cover all lines, this is simply for
	# 	debugging purposes

clean:
	# Remove all temporary files
	rm -rf \
	    $(NAME).{a,benchmark,debug,gprof,pahole,perf,so,tests} \
	    html/* *.gcda *.gcno *.rpm gmon.out pahole.txt profile.txt \
	    vgcore.*

devel-fedora:
	# Install development dependencies for Fedora Linux
	sudo dnf install valgrind dwarves gcc gdb perf gcovr \
		rpm-build firefox-wayland

gprof:
	# Profile which functions the test suite spends the most time
	# in using gprof
	$(CC) $(CC_ARGS) $(OPT_LVL) -pg $(PLAT_FLAGS) \
	    $(shell find src tests -name *.c) \
	    -Iinclude \
	    -o $(NAME).gprof
	gprof ./$(NAME).gprof > profile.txt
	less profile.txt

install:
	# Install the binary
	install -d $(DESTDIR)/$(LIBDIR)
	install $(NAME).so $(DESTDIR)/$(LIBDIR)/

install-devel:
	# Install the headers
	install -d $(DESTDIR)
	cp -r include $(DESTDIR)

lines-of-code:
	# source code
	find src -name '*.c' -exec cat {} \; | wc -l
	# tests
	find tests -name '*.c' -exec cat {} \; | wc -l
	# headers
	find include -name '*.h' -exec cat {} \; | wc -l
	# benchmarks
	find benchmark -type f -exec cat {} \; | wc -l

pahole:
	# Check struct alignnment using pahole
	$(CC) $(CC_ARGS) -O0 $(DEBUG_FLAGS) $(PLAT_FLAGS) \
	    $(shell find src tests -name *.c) \
	    -Iinclude \
	    -o $(NAME).pahole
	pahole $(NAME).pahole > pahole.txt
	less pahole.txt

perf:
	# Profile system performance counters using perf
	$(CC) $(CC_ARGS) $(OPT_LVL) $(PLAT_FLAGS) \
	    $(shell find src benchmark -name *.c) \
	    -Iinclude \
	    -DITERATIONS=$(BENCH_ITERATIONS) \
	    -DBENCH_SIZE_MB=$(BENCH_SIZE_MB) \
	    -o $(NAME).perf
	perf stat -e $(PERF_COUNTERS) ./$(NAME).perf

rpm:
	# Generate an RPM package
	$(eval version := $(shell jq .version meta.json))
	$(eval release := $(shell jq .release meta.json))
	rpmdev-setuptree
	rm -rf ~/rpmbuild/BUILD/$(NAME)*
	rm -rf ~/rpmbuild/RPMS/$(NAME)*
	cp -r . ~/rpmbuild/BUILD/$(NAME)-$(version)
	tar czf ~/rpmbuild/SOURCES/$(NAME)-$(version).tar.gz .
	rpmbuild -v -ba $(NAME).spec \
		-D "version $(version)" \
		-D "release $(release)" \
		-D "name $(NAME)"
	cp ~/rpmbuild/RPMS/$(ARCH)/$(NAME)-$(version)-1.$(ARCH).rpm .

shared:
	# Compile the shared library
	$(CC) \
	    $(CC_ARGS) $(OPT_LVL) $(PLAT_FLAGS) -shared \
	    $(shell find src -name *.c) -Iinclude -o $(NAME).so

test:
	# Compile and run the test suite through Valgrind to check for
	# memory errors, then generate an HTML code coverage report
	# using gcovr
	$(CC) $(CC_ARGS) -O0 $(DEBUG_FLAGS) $(PLAT_FLAGS) $(GCOVARGS) \
	    $(shell find src tests -name *.c) \
	    -Iinclude \
	    -o $(NAME).tests
	# If Valgrind exits non-zero, try running 'gdb ./libcds.tests'
	# to debug the test suite
	valgrind ./$(NAME).tests --track-origins=yes --leak-check=full
	mkdir html || rm -rf html/*
	gcovr -r . --exclude=bench --html --html-details -o html/coverage.html
	$(BROWSER) html/coverage.html &
