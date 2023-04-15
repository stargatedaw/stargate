#git pull
MAJOR=$(jq -r .version.major src/meta.json)
MINOR=$(jq -r .version.minor src/meta.json)
make -C src/ commit_hash
VERSION=${MAJOR}-${MINOR}
mkdir $VERSION
find $VERSION -name '*.pyc' -delete
cp -r src/{engine,files,Makefile,meta.json,scripts,sglib} $VERSION
cp -r src/{sg_py_vendor,sgui,test,vendor} $VERSION
tar czf ${VERSION}.tar.gz $VERSION
rm -rf $VERSION

