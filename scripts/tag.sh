#!/bin/sh

MAJOR=$(jq -r .version.major src/meta.json)
MINOR=$(jq -r .version.minor src/meta.json)
VERSION=${MAJOR}-${MINOR}
git tag ${VERSION}
git push --tags
