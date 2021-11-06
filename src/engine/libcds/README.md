# Work In Progress
- Nowhere near feature complete
- May change drastically (including API changes)

# libcds

libcds == C Data Structure Library

An attempt to fill that strange void in the C standard library.

# Features

- A broad selection of the most common and useful data structures
  optimized for CPU performance and efficient memory use
- 100% unit test coverage of every line of code (see `make test`)
- A benchmark suite that provides detailed micro-benchmarks of operations,
  and a working set size that can be defined at compile time using
  `BENCH_SIZE_MB=4096UL make bench`
- Various `Makefile` targets that leverage common C tools such as valgrind,
  gprof and perf.

# Documentation
## API Docs
See the headers in `include/cds`

## Developer Manual
See the `docs` folder

# Contributing

- This project has 100% unit test coverage, any new commits should
  maintain 100% coverage and zero memory errors as measured by
  `make test`.
- File an issue/FR to discuss before beginning any work on a new MR

