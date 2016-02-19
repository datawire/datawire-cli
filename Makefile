VERSION=$(shell cat VERSION)

all: init wheel local-tests

init:
	@if [ -z "$$VIRTUAL_ENV" ]; then echo "You must be in a venv for this"; false; fi
	pip install -r requirements.txt

wheel:
	python setup.py sdist bdist_wheel

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

clean:
	-find . -iname '*.pyc' -print0 | xargs -0 rm -f
	-rm -rf build

clobber: clean
	-rm -rf dist
	-rm -rf *.egg-info
