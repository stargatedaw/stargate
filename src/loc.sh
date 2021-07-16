#!/bin/sh -e

echo "Lines of C code:"
find engine/ -type f -regex '.*\.\(c\|h\)' -exec cat {} \; | wc -l

echo "C tests:"
find engine/tests -type f -regex '.*\.\(c\|h\)' -exec cat {} \; | wc -l

echo "C headers:"
find engine/include -type f -name '*.h' -exec cat {} \; | wc -l

echo "Lines of Python code"
find sgui sglib test -type f -name '*.py' -exec cat {} \; | wc -l

echo "sglib:"
find sglib -type f -name '*.py' -exec cat {} \; | wc -l

echo "sgui:"
find sgui -type f -name '*.py' -exec cat {} \; | wc -l

echo "Python tests:"
find test -type f -name '*.py' -exec cat {} \; | wc -l

