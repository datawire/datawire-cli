def checkRC(rc, what):
  if not rc:
    print("%s failed: %s" % (what, rc.error))
    return False
  else:
    return True

def checkNotRC(rc, what):
  if rc:
    print("%s should have failed but didn't: %s" % (what, rc))
    return False
  else:
    return True
