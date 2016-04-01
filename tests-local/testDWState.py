#!python

import os

import json

from DatawireState import DatawireState as qDWState
from datawire.utils.state import DataWireState as pDWState

def jsonify(obj):
  return json.dumps(obj, indent=4, separators=(',',':'), sort_keys=True)

class TestQuarkDWState (object):
  def test_defaultStatePath(self):
    qState = qDWState()
    pState = pDWState()

    mDefaultPath = os.path.join(os.path.expanduser('~'), '.datawire', 'datawire.json')
    pDefaultPath = pState.state_path

    assert(qState.defaultStatePath() == mDefaultPath)
    assert(pDefaultPath == mDefaultPath)

  def test_contents(self):
    pState = pDWState()

    pJSON = pState.toJSON()

    qState = qDWState()
    qContents = qState.defaultStateContents()
    qJSON = jsonify(json.loads(qContents))

    assert(pJSON == qJSON)

  def test_loadState(self):
    pState = pDWState()

    qState = qDWState()
    qState.loadDefaultState()

    assert(qState.getCurrentOrgID() == pState.currentOrgID())
    assert(qState.getCurrentEmail() == pState.currentOrg()['email'])

    pSvcs = pState.currentOrg()['service_tokens'].keys()
    qSvcs = qState.getCurrentServices()

    assert(jsonify(qSvcs) == jsonify(pSvcs))

    for svc in qSvcs:
      assert(qState.getCurrentServiceToken(svc) == pState.currentServiceToken(svc))

    print("-- we are [%s]%s" % (qState.getCurrentOrgID(), qState.getCurrentEmail()))
    print("-- animated: %s" % qState.getCurrentServiceToken('animated'))
