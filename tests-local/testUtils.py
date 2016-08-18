#!python

from datawire.utils import DataWireResult
from datawire.utils.random import DataWireRandom

def checkStringify(name, dwr, wanted):
    stringified = u"%s" % dwr

    if stringified != wanted:
        print("\n! %s: %s" % (name, repr(stringified)))
        print("  %s  %s" % (' ' * len(name), repr(wanted)))

    assert stringified == wanted

class TestDWUtils (object):
  def test_result(self):
    r1 = DataWireResult(ok=True, alpha="Alice", beta=True)
    assert r1
    checkStringify("r1", r1, u"<DWR OK alpha='Alice' beta=True>")

    r2 = DataWireResult(ok=False, error='Error String Here')
    assert not r2
    checkStringify("r2", r2, u"<DWR BAD error='Error String Here'>")

    r2a = DataWireResult(ok=False, error="Error String Here", extraThing="badness")
    assert not r2a
    checkStringify("r2a", r2a, u"<DWR BAD error='Error String Here' extraThing='badness'>")

    r2b = DataWireResult.fromError("Error String Here")
    assert not r2b
    checkStringify("r2b", r2b, u"<DWR BAD error='Error String Here'>")

    r2c = DataWireResult.fromError("Error String Here", errorReturn=503)
    assert not r2c
    checkStringify("r2c", r2c, u"<DWR BAD error='Error String Here' errorReturn=503>")

    r3 = DataWireResult.fromErrorAndResults(alpha="Alice", beta=True)
    assert r3
    checkStringify("r3", r3, u"<DWR OK alpha='Alice' beta=True>")

    r4 = DataWireResult.fromErrorAndResults(error="Error String Here")
    assert not r4
    checkStringify("r4", r4, u"<DWR BAD error='Error String Here'>")

    r4a = DataWireResult.fromErrorAndResults(error="Error String Here", intention=42)
    assert not r4a
    checkStringify("r4a", r4a, u"<DWR BAD error='Error String Here' intention=42>")

    r5 = DataWireResult.fromErrorAndResults(error=None, alpha="Alice", beta=True)
    assert r5
    checkStringify("r5", r5, u"<DWR OK alpha='Alice' beta=True>")

    r6 = DataWireResult.fromErrorAndResults(alpha="Alice", beta=True)
    assert r6
    checkStringify("r6", r6, u"<DWR OK alpha='Alice' beta=True>")

    r7 = DataWireResult.fromJSON(r6.toJSON())
    assert r7
    checkStringify("r7", r7, u"<DWR OK alpha=u'Alice' beta=True>")

    r8 = DataWireResult.fromErrorAndResults(error="Error String Here")
    assert not r8
    checkStringify("r8", r8, u"<DWR BAD error='Error String Here'>")

    r9 = DataWireResult.fromJSON(r8.toJSON())
    assert not r9
    checkStringify("r9", r9, u"<DWR BAD error=u'Error String Here'>")

    r8a = DataWireResult.fromErrorAndResults(error="Error String for 8a", thisIs="test 8a", andItIs="anError")
    assert not r8a
    checkStringify("r8a", r8a, u"<DWR BAD andItIs='anError' error='Error String for 8a' thisIs='test 8a'>")

    r9a = DataWireResult.fromJSON(r8a.toJSON())
    assert not r9a
    checkStringify("r9a", r9a, u"<DWR BAD andItIs=u'anError' error=u'Error String for 8a' thisIs=u'test 8a'>")

    r10a = DataWireResult.fromJSON('{"thisIs": "test 10", "andItIs": "anError", "ok": false, "error": "Error String for 10"}')
    assert not r10a
    checkStringify("r10a", r10a, u"<DWR BAD andItIs=u'anError' error=u'Error String for 10' thisIs=u'test 10'>")

  def test_randomID(self):
    """Check out random IDs."""

    randomness = DataWireRandom()

    seen = {}

    for i in range(10):
      x = randomness.randomID()

      # print(x)

      if x in seen:
        assert False

      seen[x] = True

    assert True
