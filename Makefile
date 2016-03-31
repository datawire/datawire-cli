VERSION=$(shell cat VERSION)

TESTGOLDFILE=$(shell echo /tmp/CloudTools-GOLD.$$PPID)

all: init wheel quark local-tests

.ALWAYS:

init:
	@if [ -z "$$VIRTUAL_ENV" ]; then echo "You must be in a venv for this"; false; fi
	pip install -r requirements.txt

wheel:
	python setup.py sdist bdist_wheel

develop:
	python setup.py develop

quark: .ALWAYS
	quark install quark/datawire-state-1.0.0.q

test local-tests: develop quark run-local-tests
	-rm -f $(TESTGOLDFILE)

run-local-tests:
	nosetests --with-coverage --cover-package=datawire tests-local
	python tests-local/testDWState.py > $(TESTGOLDFILE)
	node tests-local/testDWState.js $(TESTGOLDFILE)
	(cd tests-local && mvn -q test -DGoldPath=$(TESTGOLDFILE))

keyInfo:
	@if [ \( ! -d keys \) -o \
	      \( ! -s keys/dwc-identity.key \) -o \
	      \( ! -s keys/dwc-super-admin.jwt \) ]; then \
		echo "You need the Datawire Identity keys to run the remote tests." >&2 ;\
		exit 1 ;\
	fi

all-tests: develop keyInfo
	nosetests --with-coverage --cover-package=datawire tests-local tests-remote

publish: all-tests wheel
	pip install twine
	python setup.py register
	twine upload -s dist/datawire*cloud*$(VERSION)*

clean:
	-find . -iname '*.pyc' -print0 | xargs -0 rm -f
	-rm -rf build
	-rm -rf tests-local/target
	
clobber: clean
	-rm -rf dist
	-rm -rf *.egg-info
