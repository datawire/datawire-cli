from DatawireState import DatawireState

dwState = DatawireState()

print("Loading state from %s" % dwState.defaultStatePath())

dwState.loadDefaultState()

print("-- we are [%s]%s" % (dwState.getCurrentOrgID(), dwState.getCurrentEmail()))
print("-- animated: %s" % dwState.getCurrentServiceToken('animated'))
