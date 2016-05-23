VERSION=$(shell cat VERSION)

UTILSINSTALLER=https://raw.githubusercontent.com/datawire/utilities/master/install.sh

all: init local-tests install.sh

init: utilities
	@if [ -z "$$VIRTUAL_ENV" ]; then echo "You must be in a venv for this"; false; fi
	pip install -q -r requirements.txt

utilities:
	curl -lL "${UTILSINSTALLER}" | bash -s -- ${UTILSINSTALLARGS} ${UTILSBRANCH}

install.sh: utilities utilities/make_installer.py install-template.sh
	python utilities/make_installer.py \
		--template=install-template.sh \
		--modules=core,output,checks,install-python,arguments \
		--module-dir=utilities/modules \
		datawire-cli \
		https://github.com/datawire/datawire-cli/archive/master.zip \
		'$$HOME/.datawire/cli' \
		> install.sh

develop:
	python setup.py develop

test local-tests: develop
	nosetests --with-coverage --cover-package=datawire tests-local

keyInfo:
	@if [ \( ! -d keys \) -o \
	      \( ! -s keys/dwc-identity.key \) -o \
	      \( ! -s keys/dwc-super-admin.jwt \) ]; then \
		echo "You need the Datawire Identity keys to run the remote tests." >&2 ;\
		exit 1 ;\
	fi

all-tests: develop keyInfo
	nosetests --with-coverage --cover-package=datawire tests-local tests-remote

publish: all-tests install.sh
	@echo "Make sure you commit install.sh to trigger the CD pipeline."
	exit 1

clean:
	-find . -iname '*.pyc' -print0 | xargs -0 rm -f
	-rm -rf build
	-rm -rf install.sh

clobber: clean
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -rf utilities
