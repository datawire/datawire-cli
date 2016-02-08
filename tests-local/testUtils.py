#!python

from datawire.utils import DataWireResult
from datawire.utils.random import DataWireRandom

class TestDWUtils (object):
  def test_result(self):
    r1 = DataWireResult(ok=True, alpha="Alice", beta=True)
    assert r1
    assert ("%s" % r1) == u'<DWR OK alpha="Alice" beta="True">'

    r2 = DataWireResult(ok=False, error="Error String Here")
    assert not r2
    assert ("%s" % r2) == u'<DWR BAD error="Error String Here">'

    r3 = DataWireResult.fromErrorAndResults(alpha="Alice", beta=True)
    assert r3
    assert ("%s" % r3) == u'<DWR OK alpha="Alice" beta="True">'

    r4 = DataWireResult.fromErrorAndResults(error="Error String Here")
    assert not r4
    assert ("%s" % r4) == u'<DWR BAD error="Error String Here">'

    r5 = DataWireResult.fromErrorAndResults(error=None, alpha="Alice", beta=True)
    assert r5
    assert ("%s" % r5) == u'<DWR OK alpha="Alice" beta="True">'

    r6 = DataWireResult.fromErrorAndResults(alpha="Alice", beta=True)
    assert r6
    assert ("%s" % r6) == u'<DWR OK alpha="Alice" beta="True">'

    r7 = DataWireResult.fromJSON(r6.toJSON())
    assert r7
    assert ("%s" % r7) == u'<DWR OK alpha="Alice" beta="True">'

    r8 = DataWireResult.fromErrorAndResults(error="Error String Here")
    assert not r8
    assert ("%s" % r8) == u'<DWR BAD error="Error String Here">'

    r9 = DataWireResult.fromJSON(r8.toJSON())
    assert not r9
    assert ("%s" % r9) == u'<DWR BAD error="Error String Here">'

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
