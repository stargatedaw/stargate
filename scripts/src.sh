#!/bin/bash -xe

#git pull
MAJOR=$(jq -r .version.major src/meta.json)
MINOR=$(jq -r .version.minor src/meta.json)
make -C src/ commit_hash
VERSION=${MAJOR}-${MINOR}
rm -rf $VERSION
mkdir $VERSION
cp -r src/{engine,files,Makefile,meta.json,scripts,sglib} $VERSION
cp -r src/{sg_py_vendor,sgui,test,vendor} $VERSION
find $VERSION -name '*.pyc' -delete
tar czf ${VERSION}.tar.gz $VERSION
rm -rf $VERSION

