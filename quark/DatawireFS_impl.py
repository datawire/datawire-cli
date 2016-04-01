__version__ = '1.0.0';

import os

import quark

__all__ = """DatawireFS""".split(' ')

class DatawireFS (object):
    @classmethod
    def userHomeDir(klass):
        return os.path.expanduser('~')

    @classmethod
    def fileContents(klass, path):
        try:
            inputFile = open(path, "r")
            return inputFile.read()
        except Exception as e:
            runtime = quark.concurrent.Context.runtime()
            runtime.fail("failure reading %s: %s" % (path, e))
