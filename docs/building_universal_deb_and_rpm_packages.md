# Building Universal .deb and .rpm Packages
This document describes how to build packages that will be usable on a wide
variety of .rpm and .deb based Linux distros.

# How it is Done Currently
The SPEC and control files are already adequately flexible to work across the
major derivatives of Fedora, Debian and OpenSUSE.  The key to building a
single package that will work across all variants is to compile on a
sufficiently old distro with an older GCC and glibc.

Newer GCC tends to be loaded with bugs (and frankly, performance has not
increased in a meaningful way in years), and binaries compiled against glibc
are forward-compatible with newer glibc but not backwards compatible with older
glibc.  So building on an older distro is pure win, unless you are just a
software enthusiast who does not care about stability or portability and just
wants the rush of compiling against the bleeding edge.

At the moment, Debian 10 is an excellent choice, and should be for years,
perhaps until 2024 or so, at which point we may start building against
Debian 11.  Note that Debian can also build RPMs by installing the `rpm`
package.

