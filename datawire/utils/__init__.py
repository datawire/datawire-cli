import sys

import base64
import collections
import json
import time
import uuid

from jose import jwt
from jose.exceptions import JWSError

# Grumble grumble Python 2 vs 3 grumble
# (cf http://lucumr.pocoo.org/2011/1/22/forwards-compatible-python/)

class UnicodeMixin (object):
  if sys.version_info > (3, 0):
    __str__ = lambda x: x.__unicode__()
  else:
    __str__ = lambda x: unicode(x).encode('utf-8')

# We use DataWireResult in many places, so it gets to be in the toplevel datawire.utils package.

class DataWireResult (UnicodeMixin):
  def __init__(self, ok=True, error=None, **kwargs):
    self.keys = []

    if ok:
      self.ok = True

      for key in sorted(kwargs.keys()):
        self.keys.append(key)
        setattr(self, key, kwargs[key])
    else:
      self.ok = False
      self.keys = [ 'error' ]
      self.error = error

  def toDict(self):
    """ 
    Turn this result into JSON.

    It really irritates me that we need this, but the builtin JSON class simply cannot do it
    in any meaningful way. [ :P ]
    """

    dictified = { 'ok': self.ok }

    for key in self.keys:
      value = getattr(self, key)

      dictifier = getattr(value, 'toDict', None)

      if dictifier:
        dictifiedValue = dictifier()
      else:
        dictifiedValue = value

      dictified[key] = dictifiedValue

    return dictified

  def toJSON(self):
    return json.dumps(self.toDict())

  def __setitem__(self, key, value):
    setattr(self, key, value)

  def __nonzero__(self):
    return self.ok

  def __unicode__(self):
    return (u'<DWR %s %s>' % 
            ("OK" if self else "BAD",
             " ".join([ '%s="%s"' % (key, getattr(self, key)) for key in self.keys ])))

  @classmethod
  def fromError(klass, error):
    return DataWireResult(ok=False, error=error)

  @classmethod
  def OK(klass, **kwargs):
    return DataWireResult(ok=True, **kwargs)

  @classmethod
  def fromErrorAndResults(klass, error=None, **kwargs):
    if error:
      return DataWireResult(ok=False, error=error)
    else:
      return DataWireResult(ok=True, **kwargs)

  @classmethod
  def fromJSON(klass, inputJSON):
    """
    Deserialize from JSON. NOTE WELL: keys that would normally be objects (e.g. DataWireCredential)
    will deserialize as dictionaries for now.

    Also note that everywhere else, we return a DataWireResult rather than raising exceptions. In this
    case, though, raising exceptions is our only option: you have to be able to tell the difference
    between receiving valid JSON for DataWireResult that happens to have ok=False, and receiving bad JSON.
    """

    incoming = json.loads(inputJSON)

    if not isinstance(incoming, collections.Mapping):
      # WTF?
      raise TypeError("incoming JSON must be a dictionary")

    ok = incoming.get('ok', None)

    if ok is None:
      # Uh whut?
      raise ValueError("incoming JSON must have an 'ok' element")

    if not ok:
      errorMessage = incoming.get('error', None)

      if (errorMessage is None) or (not isinstance(errorMessage, basestring)):
        raise ValueError("incoming JSON with OK=False must have an 'error' element")

      # Done.
      return DataWireResult(ok=False, error=errorMessage)
    else:
      elements = { key: incoming[key] for key in incoming.keys() if key != 'ok' }

      return DataWireResult(ok=True, **elements)

# Likewise DataWireCredential.

class DataWireCredential (UnicodeMixin):
  """
  Represents a credential (for a user or a service) within the Cloud Hub.

  orgID - organization within which this cred lives
  credID - the ID of the credential itself
  scopes - valid scopes for this credential (dict with scope name as key, True value)
  ownerEmail - email of the owner of this credential

  email (required for user cred, optional otherwise) - email of the cred itself
    if email is not present for a user cred, we will raise ValueError

  tokenID (optional) - JTI for when we generate tokens; if None will be an autogenerated UUID
  iat (optional) - issued-at time, seconds since epoch; if None will be now
  nbf (optional) - not-before time, seconds since epoch; if None will be now
  """

  def __init__(self, orgID, credID, scopes, ownerEmail, email=None, tokenID=None, iat=None, nbf=None):
    if tokenID is None:
      tokenID = unicode(uuid.uuid4())

    now = int(time.time())

    if iat is None:
      iat = now

    if nbf is None:
      nbf = now

    if scopes.get('dw:user0', False) and not email:
      raise ValueError("email is required for a user credential")

    self.orgID = orgID
    self.credID = credID
    self.ownerEmail = ownerEmail
    self.scopes = scopes
    self.email = email    
    self.tokenID = tokenID
    self.iat = iat
    self.nbf = nbf

  def __unicode__(self):
    return "<DWCred %s - %s - %s>" % (self.orgID, self.credID, ",".join(sorted(self.scopes.keys())))

  def hasScope(self, scope):
    return bool(self.scopes.get(scope, False))

  def isUser(self):
    return self.hasScope('dw:user0')

  def isOrgAdmin(self):
    return self.hasScope('dw:admin0')

  def isService(self):
    return self.hasScope('dw:service0')

  def canRequestService(self):
    return self.hasScope('dw:reqSvc0')

  def getClaims(self):
    return {
      'jti': self.tokenID,
      'aud': self.orgID,
      'sub': self.credID,
      'iss': 'cloud-hub.datawire.io',
      'iat': self.iat,
      'nbf': self.nbf,
      'email': self.email,
      'ownerEmail': self.ownerEmail,
      'scopes': self.scopes,
      'dwType': 'DataWireCredential',
    }

  def toDict(self):
    return self.getClaims()

  def toJSON(self):
    return json.dumps(self.getClaims())

  def toJWT(self, privateKey, algorithm='HS256'):
    return jwt.encode(self.getClaims(), privateKey, algorithm=algorithm)

  @classmethod
  def fromJSON(self, inputJSON, needOrgID):
    claims = json.loads(inputJSON)

    return DataWireCredential.fromClaims(claims, needOrgID)

  @classmethod
  def fromClaims(self, claims, needOrgID):
    cred = None
    errorMessage = None
    badElements = []

    dwType = claims.get('dwType', None)
    tokenID = claims.get('jti', None)
    orgID = claims.get('aud', None)
    credID = claims.get('sub', None)
    issuer = claims.get('iss', None)
    iat = claims.get('iat', None)
    nbf = claims.get('nbf', None)
    email = claims.get('email', None)
    ownerEmail = claims.get('ownerEmail', None)
    scopes = claims.get('scopes', None)

    now = int(time.time())

    if dwType != 'DataWireCredential':
      badElements.append('dwType')

    if not tokenID:
      badElements.append('tokenID')

    if orgID != needOrgID:
      badElements.append('orgID (must be %s)' % needOrgID)

    if issuer != 'cloud-hub.datawire.io':
      badElements.append('issuer (must be cloud-hub.datawire.io)')

    if (not isinstance(iat, int)) or (iat > (now + 30)):
      badElements.append('iat (must not be in the future)')

    if (not isinstance(nbf, int)) or (nbf > (now + 30)):
      badElements.append('nbf (must not be in the future)')

    if not credID:
      badElements.append('credID')

    if not ownerEmail:
      badElements.append('ownerEmail')

    if not scopes:
      badElements.append('scopes')

    if scopes.get('dw:user0', False) and not email:
      badElements.append('email (required for user credential)')

    if badElements:
      errorMessage = 'required fields missing or incorrect: %s' % (' '.join(badElements))
    else:
      # All good.
      cred = DataWireCredential(orgID, credID, scopes, ownerEmail,
                                email=email, tokenID=tokenID, iat=iat, nbf=nbf)

    return DataWireResult.fromErrorAndResults(error=errorMessage, cred=cred)

  @classmethod
  def fromJWT(self, token, publicKey, needOrgID, algorithm='HS256',
              really_dont_verify_tokens=False):
    """
    Decode a JWT into a credential. You must know the orgID for which the
    cred should have been issued, because we need to verify that it matches.

    Returns a DataWireResult with a cred member on success.
    """

    cred = None
    claims = None
    errorMessage = None

    try:
      if not publicKey:
        if not really_dont_verify_tokens:
          errorMessage = "public key is required to decode JWT"
        else:
          # Brutal hackery here.
          fields = token.split('.')

          if len(fields) != 3:
            errorMessage = "malformed token (must have three fields)"
          elif not fields[0]:
            errorMessage = "malformed token (header field not present)"
          elif not fields[1]:
            errorMessage = "malformed token (claims field not present)"
          else:
            b64Header = fields[0]
            b64Claims = fields[1]

            while len(b64Header) % 3:
              b64Header += '='

            while len(b64Claims) % 3:
              b64Claims += '='

            header = json.loads(base64.b64decode(b64Header))

            if (('typ' not in header) or (header['typ'] != 'JWT')):
              errorMessage = 'malformed token (not a JWT)'
            elif (('alg' not in header) or (header['alg'] != 'HS256')):
              errorMessage = 'malformed token (not HS256)'
            else:
              claims = json.loads(base64.b64decode(b64Claims))
      else:
        claims = jwt.decode(token, publicKey,
                            algorithms=algorithm,
                            audience=needOrgID,
                            issuer='cloud-hub.datawire.io')
    except JWSError as error:
      errorMessage = error.message

    if claims:
      rc = DataWireCredential.fromClaims(claims, needOrgID)

      if rc:
        cred = rc.cred
      else:
        errorMessage = rc.error

    return DataWireResult.fromErrorAndResults(error=errorMessage, cred=cred)
