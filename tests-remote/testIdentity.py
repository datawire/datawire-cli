#!python

import sys

import json
import time
import requests

from datawire.utils import DataWireResult, DataWireCredential
from datawire.utils.tests import checkRC, checkNotRC
from datawire.utils.keys import DataWireKey

# # We need DataWireCredential for real.
# from DWCloud.registrar import DataWireRegistrar, DataWireOrg

# # We only import DataWireAuth0 for a hackish way to clean up.
# from DWCloud.dwAuth0 import DataWireAuth0

from datawire.cloud.identity import Identity

# BaseURL = "https://id.datawire.io"
BaseURL = "http://localhost:8080"

def basicSetup():
  # Grab the public key...
  rc = DataWireKey.load_public('keys/dwc-identity.key')

  if not rc:
    return DataWireResult.fromError("no public key: %s" % rc.error)

  dwc = Identity(BaseURL, key=rc.publicKey)

  # To do our tests, we need the magic super-admin JWT too.

  superToken = open("keys/dwc-super-admin.jwt", "r").read().strip()

  return DataWireResult(ok=True, dwc=dwc, superToken=superToken)

class TestDataWireRegistrarClientMethods (object):
  def test_makeURL(self):
    rc = basicSetup()

    assert checkRC(rc, "basic setup")

    url = rc.dwc.makeURL("auth", "_000000000", "alice")
    assert url == (BaseURL + "/auth/_000000000/alice")

class TestRegistrationService (object):
  @classmethod
  def orgCreated(klass, orgID, orgName, adminEmail, adminToken):
    # Yes, I mean to be appending a tuple here.
    klass.orgsCreated.append((orgID, orgName, adminEmail, adminToken))  # see comment above

    # Also set up a dict so we can find the org for later tests.
    klass.orgMap[orgName] = orgID

  @classmethod
  def setup_class(klass):
    """ Run once per test class before any tests are run """
    rc = basicSetup()

    assert checkRC(rc, "basic setup")

    klass.orgsCreated = []
    klass.orgMap = {}

    klass.dwc = rc.dwc
    klass.superToken = rc.superToken

    # Create a new org.
    rc = klass.dwc.orgCreate("Alice's House of Grues",
                             "Alice", "alice@test.datawire.io", "aliceRules",
                             isATest=True)

    assert checkRC(rc, "create org")

    klass.orgID = rc.orgID
    assert klass.orgID

    klass.orgAdminCred = rc.cred
    assert klass.orgAdminCred

    klass.orgAdminToken = rc.token
    assert klass.orgAdminToken

    klass.orgCreated(klass.orgID, "Alice's House of Grues",
                     "alice@test.datawire.io", klass.orgAdminToken)

  @classmethod
  def teardown_class(klass):
    """ Run once per test class after all tests are run """
    # Hackish way to delete the org we've just created.
    print("settling the world")

    # Let the world settle.
    time.sleep(2)

    for orgID, orgName, adminEmail, adminToken in klass.orgsCreated:
      print("smiting %s -- %s" % (orgID, orgName))
      klass.dwc.orgDelete(orgID, superToken=klass.superToken)

  def setup(self):
    """ Run once before each test """

    # Copy stuff to save typing.
    self.dwc = TestRegistrationService.dwc
    self.superToken = TestRegistrationService.superToken

    self.orgID = TestRegistrationService.orgID
    self.orgAdminCred = TestRegistrationService.orgAdminCred
    self.orgAdminToken = TestRegistrationService.orgAdminToken

  def teardown(self):
    """ Run once after each test """
    pass

  def test_100_createUsers(self):
    usersToCreate = [
      ("Bob", "bob@test.datawire.io", "bobRules"),
      ("Eve", "eve@test.datawire.io", "eveRules"),
      ("Mallet", "mallet@test.datawire.io", "malletRules"),
    ]

    invitations = []

    for fullName, email, password in usersToCreate:
      # Invite the user...
      rc = self.dwc.userInvite(self.orgID, self.orgAdminToken, email, scopes=[ 'dw:reqSvc0' ])

      assert rc
      assert rc.invitation

      invitation = rc.invitation

      # Tuples FTW
      invitations.append((email, fullName, password, invitation))

    # Let the world settle...
    time.sleep(5)

    # ...then accept the invitations.

    for email, fullName, password, invitation in invitations:
      rc = self.dwc.userAcceptInvitation(invitation, fullName, password)

      assert rc

      # If rc is good, we know that self.dwc.userCreate has vetted the returned token, etc.
      # We'll just assert that they exist here.

      assert rc.orgID
      assert rc.cred
      assert rc.token

  def test_200_goodAuth(self):
    rc = self.dwc.userAuth('alice@test.datawire.io', 'aliceRules')

    assert checkRC(rc, "userAuth alice")
    assert rc.orgID == self.orgID

    assert rc.cred
    assert rc.token

  def test_201_badAuth(self):
    rc = self.dwc.userAuth('bob@test.datawire.io', 'aliceRules')

    assert checkNotRC(rc, "bad userAuth bob")

  def test_300_serviceCreate(self):
    # Explicitly auth as Eve
    rc = self.dwc.userAuth('eve@test.datawire.io', 'eveRules', orgID=self.orgID)

    assert checkRC(rc, "userAuth eve")
    assert rc.orgID == self.orgID

    assert rc.cred
    assert rc.token

    # Try for a service.
    rc = self.dwc.serviceCreate(self.orgID, rc.token, 'grueLocator')

    assert checkRC(rc, "serviceCreate grueLocator")

    assert rc.cred

    svcToken = rc.token
    assert svcToken

    rc = self.dwc.serviceCheck(self.orgID, svcToken, 'grueLocator')

    assert checkRC(rc, "serviceCheck grueLocator")

    rc = self.dwc.serviceCheck(self.orgID, svcToken, 'grueAvoider')

    assert checkNotRC(rc, "serviceCheck grueAvoider")

    rc = self.dwc.serviceCheck(self.orgID, svcToken + svcToken, 'grueLocator')

    assert checkNotRC(rc, "serviceCheck bad token (1)")

    c = chr(ord(svcToken[52]) + 1)

    badToken = svcToken[0:52] + c + svcToken[53:]

    rc = self.dwc.serviceCheck(self.orgID, badToken, 'grueLocator')

    assert checkNotRC(rc, "serviceCheck bad token (2)")

  def test_400_orgsList(self):
    # Create some new orgs.
    for orgName, adminName, adminEmail, adminPassword in [
      ( "Bob's House o' Fishin' Tackle n' Certifyin' Authori-tie",
        'Bob', 'bob-ftca@test.datawire.io', 'bobRules' ),
      ( "Eve's Espionage Emporium",
        'Eve', 'eve-eee@test.datawire.io', 'eveRules' ),
      ( "Mallet's Hardware Hut",
        'Mallet', 'mallet-hh@test.datawire.io', 'malletRules' ),
      ( "Alice's Grue Supply",
        'Alice', 'alice-grue@test.datawire.io', 'aliceRules' )
    ]:
      rc = self.dwc.orgCreate(orgName, adminName, adminEmail, adminPassword, isATest=True)

      assert checkRC(rc, "create org")

      assert rc.orgID
      assert rc.cred
      assert rc.token

      TestRegistrationService.orgCreated(rc.orgID, orgName, adminEmail, rc.token)

    # Let the world settle. Sigh.
    print("settling the world")
    time.sleep(5)

    # After creating the orgs, try for a list.
    #
    # XXX
    # For right now this uses a magic super-admin token which you cannot get via the
    # registrar. It must be generated OOB by hand. Talk to Flynn about how.

    rc = self.dwc.orgList(self.superToken)

    assert checkRC(rc, "list orgs")

    assert rc.orgIDs

    createdOrgIDs = [ orgTuple[0] for orgTuple in TestRegistrationService.orgsCreated]
    createdList = ",".join(sorted(createdOrgIDs))
    readList = ",".join(sorted(rc.orgIDs))

    if createdList != readList:
      print("Created orgs: %s" % createdList)
      print("Read back:    %s" % readList)

    assert createdList == readList
