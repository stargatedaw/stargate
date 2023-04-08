#!/bin/sh -xe

# Currently working on Debian 11

# Build the rpm and deb packages and copy to /mnt/stargatedaw
# Meant for building the rpm and deb packages on an old version of Debian,
# so that they will be linked against an old glibc and in theory run on
# any Linux distro that uses those package formats

cd $(realpath $(dirname $0)/..)

git switch main
git pull
./scripts/deb.py -i
./scripts/rpm.py

MINOR=$(jq -r .version.minor src/meta.json)
cp \
	src/stargate-${MINOR}-*amd64.deb \
	stargate-${MINOR}-1.x86_64.rpm \
	/mnt/stargatedaw/
