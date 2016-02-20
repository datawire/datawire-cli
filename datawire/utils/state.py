import sys

import os
import errno
import json

class DataWireError (Exception):
  pass

class DataWireNoCurrentOrgError (DataWireError):
  pass

class DataWireNoCurrentUserTokenError (DataWireError):
  pass

class DataWireNoSuchServiceError (DataWireError):
  pass

class DataWireState (object):
  def __init__(self, statePath=None):
    # Make sure we have ~/.datawire...
    if statePath:
      self.state_path = statePath
      self.state_dir = os.path.dirname(os.path.abspath(self.state_path))
    else:
      self.state_dir = os.path.join(os.path.expanduser('~'), '.datawire')
      self.state_path = os.path.join(self.state_dir, "datawire.json")

    self.state = {}
    self.dirty = False

    inFile = None

    try:
      inFile = open(self.state_path, "r")
    except IOError as exception:
      if exception.errno != errno.ENOENT:
        self.warn("open", self.state_path, exception)

    if inFile != None:
      try:
        self.state = json.load(inFile)
      except ValueError as exception:
        self.warn("load", self.state_path, exception)
      except IOError as exception:
        self.warn("read", self.state_path, exception)

    if inFile != None:
      inFile.close()

  def __len__(self):
    return len(self.state)

  def __getitem__(self, key):
    return self.state.get(key, None)

  def __setitem__(self, key, value):
    self.state[key] = value
    self.dirty = True

  def __delitem__(self, key):
    del(self.state[key])
    self.dirty = True

  def __iter__(self):
    return self.state.__iter__()

  def __contains__(self, key):
    return key in self.state

  def keys(self):
    return self.state.keys()

  def save(self):
    haveStateDir = False

    try:
      os.makedirs(self.state_dir)
      haveStateDir = True
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        self.warn("create", self.state_dir, exception)
      else:
        haveStateDir = True

    if haveStateDir:
      try:
        outFile = open(self.state_path, "w")
        outFile.write(self.toJSON())
        outFile.close()
        self.dirty = False
      except IOError as exception:
        self.warn("save state to", self.state_path, exception)

  def toJSON(self):
    return json.dumps(self.state, indent=4, separators=(',',':'), sort_keys=True)

  def smite(self):
    """ USE WITH CARE """
    try:
      os.remove(self.state_path)
    except OSError as exception:
      if exception.errno != errno.ENOENT:
        raise

    self.state = []
    self.dirty = True

  def warn(self, verb, path, exception):
    sys.stderr.write("WARNING: could not %s %s\n    (%s)\n" %
                     (verb, path, exception))
    sys.stderr.write("Your Datawire account state will not be persistent. This may make other\n")
    sys.stderr.write("Datawire tools unhappy.\n")

  def currentOrgID(self):
    if 'orgID' not in self:
      raise DataWireNoCurrentOrgError("no current org")

    return self['orgID']

  def currentOrg(self):
    orgID = self.currentOrgID()

    if 'orgs' not in self:
      raise DataWireNoCurrentOrgError("no orgs at all")

    return self['orgs'][orgID]

  def currentUserToken(self):
    orgID = self.currentOrgID()
    org = self.currentOrg()

    if 'user_token' not in org:
      raise DataWireNoCurrentUserTokenError("no user token for org %s" % orgID)

    return org['user_token']

  def currentServiceToken(self, serviceName):
    org = self.currentOrg()

    if not org:
      raise DataWireNoCurrentOrgError("no current org")

    if 'service_tokens' not in org:
      raise DataWireNoSuchServicError("no services in current org")

    service_tokens = org['service_tokens']

    if serviceName not in service_tokens:
      raise DataWireNoSuchServicError("no such service in current org")

    return service_tokens[serviceName]

# def now8601():
#     # Yeek.
#     return datetime.datetime.now(dateutil.tz.tzlocal()).isoformat()

# def osVersion():
#     sysName = platform.system()

#     if sysName == 'Darwin':
#         release, versioninfo, machine = platform.mac_ver()

#         return "MacOS X %s (%s)" % (release, machine)
#     else:
#         # Should be Linux

#         distname, version, id = platform.linux_distribution()

#         if distname:
#             return "%s %s (%s)" % (distname, version, platform.machine())
#         else:
#             # Oh well.
#             return "%s %s (%s)" % (sysName, platform.release(), platform.machine())

# def pythonVersion():
#     return "Python %s" % platform.python_version()
