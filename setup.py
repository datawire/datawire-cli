from setuptools import setup, find_packages

VERSION = open('VERSION', 'r').read().strip()

setup(
    name = "datawire-cloudtools",
    version = VERSION,
    packages = find_packages(),
    scripts = [ 'dwc' ],

    install_requires = [ 
        'requests==2.9.1',
        'python-jose==0.5.5'
    ],

    package_data = {
        # # If any package contains *.txt or *.rst files, include them:
        # '': ['*.txt', '*.rst'],
        # # And include any *.msg files found in the 'hello' package, too:
        # 'hello': ['*.msg'],
    },

    # metadata for upload to PyPI
    author = "Flynn",
    author_email = "flynn@datawire.io",
    description = "Datawire Cloud Tools",
    license = "Closed beta. Contact author with requests.",
    keywords = "datawire cloud tools",
    url = "http://datawire.io/",   # project home page, if any
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: Other/Proprietary License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # could also include download_url, etc.

    long_description = """BETA SOFTWARE. Contact Datawire before use.

    This is the set of tools for interacting with the Datawire Cloud."""
)
