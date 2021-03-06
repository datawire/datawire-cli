#!python

import logging
import requests

"""
DataWireRegistrar client
"""

from ..utils import DataWireResult, DataWireCredential # Needs to move to .utils

class DataWireIdentityError (Exception):
  pass

class DataWireIdentityNoKeyError (DataWireIdentityError):
  pass

class Identity (object):
  def __init__(self, baseURL, key, really_dont_verify_tokens=False):
    self.baseURL = baseURL
    self.publicKey = key

    if (key is None) and not really_dont_verify_tokens:
      raise DataWireIdentityNoKeyError("Identity requires public key for token verification")

  def makeURL(self, *elements):
    return "%s/%s" % (self.baseURL, "/".join(elements))

  def httpParams(self, target, token):
    url = self.makeURL(*target)
    headers = None

    if token is not None:
      headers = {
        'Authorization': 'Bearer ' + token
      }
  
    return url, headers    

  def checkResponse(self, url, resp, required=None):
    status = resp.status_code
    result = None

    try:
      result = resp.json()
    except ValueError:
      pass

    # print("%s: %d -- %s" % (url, status, result))

    if not result:
      # Hrm.
      return DataWireResult.fromError('No result from request (status %d)!' % status)

    # OK. Did it work?
    ok = result.get('ok', False)

    if not ok:
      return DataWireResult.fromError(result.get('error', 'request failed!'))

    # OK, if here, the claim is that it worked.

    missingElements = []

    for key in required:
      if result.get(key, None) is None:
        missingElements.append(key)

    if missingElements:
      return DataWireResult.fromError('missing response elements: %s' % " ".join(missingElements))

    # Finally!
    return DataWireResult(**result)

  def get(self, target=None, required=None, token=None):
    """
    GET from an endpoint that will respond with a JSON-encoded DataWireResult.

    Returns a DataWireResult, after making sure that all the requiredResults are present
    in the DataWireResult.
    """

    url, headers = self.httpParams(target, token)
    resp = requests.get(url, headers=headers)

    return self.checkResponse(url, resp, required=required)

  def post(self, target=None, args=None, required=None, token=None):
    """
    POST to an endpoint that will respond with a JSON-encoded DataWireResult.

    Returns a DataWireResult, after making sure that all the requiredResults are present
    in the DataWireResult.
    """

    url, headers = self.httpParams(target, token)
    resp = requests.post(url, json=args, headers=headers)

    return self.checkResponse(url, resp, required=required)

  def put(self, target=None, args=None, required=None, token=None):
    """
    PUT to an endpoint that will respond with a JSON-encoded DataWireResult.

    Returns a DataWireResult, after making sure that all the requiredResults are present
    in the DataWireResult.
    """

    url, headers = self.httpParams(target, token)
    resp = requests.put(url, json=args, headers=headers)

    return self.checkResponse(url, resp, required=required)

  def delete(self, target=None, args=None, required=None, token=None):
    """
    DELETE to an endpoint that will respond with a JSON-encoded DataWireResult.

    Returns a DataWireResult, after making sure that all the requiredResults are present
    in the DataWireResult.
    """

    url, headers = self.httpParams(target, token)
    resp = requests.delete(url, json=args, headers=headers)

    return self.checkResponse(url, resp, required=required)

  def credentialFromToken(self, token, orgID):
    # First, is the credential valid?

    really_dont_verify_tokens = False

    if not self.publicKey:
      really_dont_verify_tokens = True

    return DataWireCredential.fromJWT(token, self.publicKey, orgID,
                                      really_dont_verify_tokens=really_dont_verify_tokens)

  def checkToken(self, token, orgID, scopesMust, scopesMustNot):
    # Try to grab the credential underlying our token...

    rc = self.credentialFromToken(token, orgID)

    if not rc:
      # Well that ain't good.
      return rc

    # OK! Time to check to make sure the scopes match.
    cred = rc.cred

    missingScopes = [ scope for scope in scopesMust if not cred.hasScope(scope) ]

    if missingScopes:
      return DataWireResult.fromError('credential is missing scopes: %s' % " ".join(missingScopes))

    wrongScopes = [ scope for scope in scopesMustNot if cred.hasScope(scope) ]

    if wrongScopes:
      return DataWireResult.fromError('credential must not have scopes: %s' % " ".join(wrongScopes))

    # All good.
    return DataWireResult(ok=True, cred=cred)

  def checkOrgAdmin(self, token, orgID):
    return self.checkToken(token, orgID, 
                           [ 'dw:user0', 'dw:admin0', 'dw:reqSvc0' ], # must have these
                           [ 'dw:organization0', 'dw:service0' ]      # must not have these
                          )

  def checkCanRequestServices(self, token, orgID):
    return self.checkToken(token, orgID, 
                           [ 'dw:reqSvc0' ],                          # must have these
                           []                                         # must not have these
                          )
  def checkUser(self, token, orgID):
    return self.checkToken(token, orgID, 
                           [ 'dw:user0' ],                            # must have these
                           [ 'dw:organization0', 'dw:service0' ]      # must not have these
                          )

  def checkService(self, token, orgID):
    return self.checkToken(token, orgID, 
                           [ 'dw:service0' ],                         # must have these
                           [ 'dw:organization0', 'dw:user0', 'dw:reqSvc0' ] # must not have these
                          )

  def orgList(self, superToken):
    rc = self.get( target=[ 'v1', 'orgs' ],
                   token=superToken,
                   required=[ 'orgIDs' ]
                  )

    return rc

  def orgDelete(self, orgID, superToken):
    rc = self.delete( target=[ 'v1', 'orgs', orgID ],
                      token=superToken,
                      required=[ 'count' ]
                    )

    return rc

  def orgCreate(self, orgName, adminName, adminEmail, adminPassword, isATest=False, reason=None):
    args={
      "orgName": orgName,
      "adminName": adminName,
      "adminEmail": adminEmail,
      "adminPassword": adminPassword,
      "isATest": isATest
    }

    if reason:
      args['reason'] = reason

    rc = self.post( target=[ 'v1', 'orgs' ],
                    args=args,
                    required=[ 'orgID', 'token' ]
                  )

    if not rc:
      return rc

    # OK, if here, we have an orgID and a token. Is the token valid?
    token = rc.token
    orgID = rc.orgID
    meta = rc.meta
    userHash = rc.userHash
    createdAt = rc.createdAt

    logging.info("created %s: %s - %s" % (orgName, orgID, token))

    rc = self.checkOrgAdmin(token, orgID)

    if not rc:
      return rc

    # Finally!
    return DataWireResult(ok=True, orgID=orgID, token=token, meta=meta, userHash=userHash, createdAt=createdAt,
                          cred=rc.cred)

  def userInvite(self, orgID, token, email, adminName, adminEmail,
                 message=None, scopes=None):
    rc = self.post( target=[ 'v1', 'users', orgID ],
                    token=token,
                    args={
                      "adminName": adminName,
                      "adminEmail": adminEmail,
                      "email": email,
                      "message": message,
                      "scopes": scopes
                    },
                    required=[ 'orgID', 'invitation' ]
                  )

    return rc

  # userAcceptInvitation, userAuth, and userUpdate all return exactly the same thing.
  # self.userCommonResult() is the way we manage that.
  def userCommonResult(self, rc):
    # If this is a failure, short-circuit.
    if not rc:
      return rc

    # Every common-result function hands back an rc with an orgID, email, token, and metadata.
    # Break 'em out...

    orgID = rc.orgID
    email = rc.email
    token = rc.token
    meta = rc.meta
    userHash = rc.userHash
    createdAt = rc.createdAt

    # Next up, make sure the token belongs to this org, and is a valid user token. 
    #
    # NOTE WELL: we overwrite rc here. The new rc has a credential instead of the token.
    rc = self.checkUser(token, orgID)

    if not rc:
      # Oops.
      return rc

    # Finally!
    cred = rc.cred

    return DataWireResult(ok=True, orgID=orgID, email=email, meta=meta, token=token, userHash=userHash, 
                          createdAt=createdAt, cred=cred)

  def userAcceptInvitation(self, invitation, name, password):
    rc = self.put( target=[ 'v1', 'invitations', invitation ],
                   args={
                     "name": name,
                     "password": password
                   },
                   required=[ 'orgID', 'email', 'token' ]
                 )

    return self.userCommonResult(rc)

  def userUpdate(self, orgID, token, email, name=None, password=None, meta=None):
    args = {
      "name": name,
      "password": password
    }

    if meta:
      args['meta'] = meta

    rc = self.put( target=[ 'v1', 'users', orgID, email ],
                   token=token,
                   args=args,
                   required=[ 'orgID', 'token' ]
                 )

    return self.userCommonResult(rc)

  def userAuth(self, email, password, orgID=None, doppelganger=None):
    args = { 'password': password }

    if orgID is not None:
      args['orgID'] = orgID

    if doppelganger:
      args['doppelganger'] = doppelganger

    rc = self.post( target=[ 'v1', 'auth', email ],
                    args=args,
                    required=[ 'orgID', 'email', 'token' ]
                  )

    return self.userCommonResult(rc)

  def userForgotPassword(self, email, orgID=None):
    args=None

    if orgID is not None:
      args = { 'orgID': orgID }

    rc = self.post( target=[ 'v1', 'forgot', email ],
                    args=args,
                    required=[ 'msg' ]
                  )

    return rc

  def serviceCreate(self, orgID, token, serviceHandle):
    rc = self.post( target=[ 'v1', 'services', orgID ],
                    token=token,
                    args={
                      "serviceHandle": serviceHandle,
                    },
                    required=[ 'orgID', 'token' ]
                  )

    if not rc:
      return rc

    # OK, if here, we have an orgID and a token. Is the token valid?
    token = rc.token
    orgID = rc.orgID

    rc = self.checkService(token, orgID)

    if not rc:
      return rc

    # Finally!
    cred = rc.cred

    return DataWireResult(ok=True, token=token, cred=cred, orgID=orgID)

  def serviceCheck(self, orgID, token, serviceHandle):
    rc = self.post( target=[ 'v1', 'svcCheck', orgID, serviceHandle ],
                    token=token,
                    required=[ 'orgID' ]
                  )

    return rc
