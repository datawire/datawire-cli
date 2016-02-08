from setuptools import setup, find_packages

VERSION = open('VERSION', 'r').read().strip()

setup(
    name = "datawire-cloudtools",
    version = VERSION,
    packages = find_packages(),
    scripts = [ 'dwc' ],

    install_requires = [ 
        'requests>=2.9.1',
        'python-jose>=0.5.5'
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
    license = "PSF",
    keywords = "datawire cloud tools",
    url = "http://datawire.io/",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.

    long_description = "This is the set of tools for interacting with the Datawire Cloud.",
)
