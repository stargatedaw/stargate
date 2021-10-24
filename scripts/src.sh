#git pull
MAJOR=$(jq -r .version.major src/meta.json)
MINOR=$(jq -r .version.minor src/meta.json)
make -C src/ commit_hash
VERSION=${MAJOR}-${MINOR}
cp -r src $VERSION
tar czf ${VERSION}.tar.gz $VERSION
rm -rf $VERSION

