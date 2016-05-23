#!/bin/bash

set -e
set -o pipefail

step () {
	echo "==== $@"
}

msg () {
	echo "== $@"
}

# make does everything we need right now.
step "Initializing build environment"

# Create a shiny new virtualenv for ourselves to work in.
msg "virtualenv..."

virtualenv .autobuild-venv
. .autobuild-venv/bin/activate

# Initialize our world
make init

step "Work out next version"

CURRENT_BRANCH=${GIT_BRANCH##*/}

if [ $CURRENT_BRANCH = "develop" ]; then
	VERSION=$(python ./utilities/versioner.py --verbose)
else
	VERSION=$(python ./utilities/versioner.py --verbose --magic-pre)
fi

if [ -z "$VERSION" ]; then
	step "Skipping build"
	exit 1
fi

step "Building ${VERSION} on ${CURRENT_BRANCH} at ${GIT_COMMIT}"

msg "updating VERSION"

echo "${VERSION}" > VERSION

msg "make local-tests"
make local-tests

step "Tagging v${VERSION}"

git tag -a "v${VERSION}" -m "v${VERSION} by Jenkins" "${GIT_COMMIT}"
git push --tags origin

step "Merging into master"

git checkout -- VERSION

set -x 

git checkout master
git merge --ff-only --commit --stat origin/develop
git push origin

