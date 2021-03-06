import sys

import base64
import collections
import json
import time
import types
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

def prettyJSON(obj):
  return json.dumps(obj, indent=4, separators=(',',':'), sort_keys=True)

# We use DataWireResult in many places, so it gets to be in the toplevel datawire.utils package.

class DataWireResult (UnicodeMixin):
  def __init__(self, ok=True, error=None, **kwargs):
    # OK, what gives? Why are we doing all this craziness with setattr plus a keydict and things like
    # that? Well, we have a couple of goals here:
    # 
    # 1. If we do
    #
    #    result = DatawireResult.OK(goodThings=True, badThings=False)
    #
    # then we want both result.goodThings and result['goodThings'] to work, for setting or for getting,
    # and we also want 
    #
    #    if "goodThings" in result: ...
    #
    # to work too. It turns out to be quite painful to make that work by overriding the . operator to look
    # into a dict, but easy to do it by overriding the [] operator to look at object attributes... except 
    # that the 'in' business is annoying to do without also having a separate stash of keys, and iterating 
    # the set of keys that the user passed in is bloody impossible without a separate stash of keys.
    #
    # SO. self._keys is just a set of which keys are present. Attributes on self store the actual values.

    self._keys = set()

    if ok:
      self.ok = True
      self.error = None     # you can't set ok and error at the same time
    else:
      self.ok = False

      self['error'] = error

    for key in kwargs:
      self[key] = kwargs[key]

  def toDict(self):
    """ 
    Turn this result into JSON.

    It really irritates me that we need this, but the builtin JSON class simply cannot do it
    in any meaningful way. [ :P ]
    """

    dictified = { 'ok': self.ok }

    for key in self._keys:
      value = self[key]

      dictifier = getattr(value, 'toDict', None)

      if dictifier:
        dictifiedValue = dictifier()
      else:
        dictifiedValue = value

      dictified[key] = dictifiedValue

    return dictified

  def toJSON(self):
    return json.dumps(self.toDict())

  def keys(self):
    return iter(self._keys)

  def __setitem__(self, key, value):
    self._keys.add(key)
    setattr(self, key, value)

  def __getitem__(self, key):
    return getattr(self, key)

  def __contains__(self, key):
    return key in self._keys

  def __nonzero__(self):
    return self.ok

  def __unicode__(self):
    return (u'<DWR %s %s>' % 
            ("OK" if self else "BAD",
             " ".join([ '%s=%s' % (key, repr(getattr(self, key))) for key in sorted(self._keys) ])))

  @classmethod
  def fromError(klass, error, **kwargs):
    return DataWireResult(ok=False, error=error, **kwargs)

  @classmethod
  def OK(klass, **kwargs):
    return DataWireResult(ok=True, **kwargs)

  @classmethod
  def fromErrorAndResults(klass, error=None, **kwargs):
    if error:
      return DataWireResult(ok=False, error=error, **kwargs)
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
    errorMessage = None

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
        # You can't have a key that's not OK and has no error.
        raise ValueError("incoming JSON with OK=False must have an 'error' element")

    # OK, all's well. Make a copy of the incoming dict and smite the 'ok' and 'error' keys,
    # since they don't get passed to the constructor as keyword args.

    elements = dict(incoming);

    if 'ok' in elements:
      del(elements['ok'])

    if 'error' in elements:
      del(elements['error'])

    return DataWireResult(ok=ok, error=errorMessage, **elements)

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
  exp (optional) - expiration time, seconds since epoch; if None, token will not expire
  """

  prettyScopeNames = {
    'dw:admin0': 'Organization administrator',
    'dw:organization0': 'Organization',
    'dw:reqSvc0': 'Able to request service tokens',
    'dw:service0': 'Service',
    'dw:user0': 'User',
    'dw:doppelganger0': 'Doppelgangers welcome'
  }

  def __init__(self, orgID, credID, scopes, ownerEmail, email=None, tokenID=None, iat=None, nbf=None, exp=None):
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
    self.expiry = exp

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
    claims = {
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

    if self.expiry is not None:
      claims['exp'] = self.expiry

    return claims

  def toDict(self):
    return self.getClaims()

  def toJSON(self):
    return json.dumps(self.getClaims())

  def toJWT(self, privateKey, algorithm='HS256'):
    return jwt.encode(self.getClaims(), privateKey, algorithm=algorithm)

  @classmethod
  def prettyScopeName(self, scope):
    return self.prettyScopeNames.get(scope, '')

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
    exp = claims.get('exp', None)
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

    if ((exp is not None) and 
        ((not isinstance(exp, int)) or (exp < (now - 30)))):
      badElements.append('exp (must not be in the past)')

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
                                email=email, tokenID=tokenID,
                                iat=iat, nbf=nbf, exp=exp)

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
          header = jwt.get_unverified_headers(token)

          if (('typ' not in header) or (header['typ'] != 'JWT')):
            errorMessage = 'malformed token (not a JWT)'
          elif (('alg' not in header) or (header['alg'] != 'HS256')):
            errorMessage = 'malformed token (not HS256)'
          else:
            claims = jwt.get_unverified_claims(token)
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
