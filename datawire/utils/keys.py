#!python

import sys

import base64
# import collections
import json

# from . import UnicodeMixin

class DataWireKeyError (Exception):
  pass

class DataWireKeyUnimplementedError (DataWireKeyError):
  pass

class DataWireKeyBadFormatError (DataWireKeyError):
  pass

class DataWireHMACKey (object):
  def __init__(self, key=None):
    """
    This is not the entry point you want. Check out DataWireHMACKey.new() and 
    DataWireHMACKey.load().
    """
    self.key = key

  def encoded(self):
    return base64.urlsafe_b64encode(self.key)

  @classmethod
  def new(self, bits=384, randomness=None):
    """ 
    Generates a new random HMAC key with the specified number of bits and
    returns it as a string, encoded per RFC4648 section 5 (base64 with the alternate,
    URL-safe, alphabet).
    """

    if not randomness:
      randomness = DataWireRandom()

    return DataWireHMACKey(key=randomness.randomBitString(bits))

  @classmethod
  def decode(encodedKey):
    """
    Accepts an HMAC key encoded per RFC4648 section 5 and returns the corresponding
    raw key bits.
    """

    return DataWireHMACKey(key=base64.urlsafe_b64decode(encodedKey))

  @classmethod
  def load(path):
    """ Load an HMAC key from path """
    encodedKey = open(path, "r").read().strip()

    return DataWireHMACKey.decode(encodedKey)

class DataWireRSAKey (object):
  def __init__(self, public_key=None, private_key=None):
    """
    This is not the entry point you want. Check out DataWireHRSAKey.new(),
    DataWireRSAKey.load(). and DataWireRSAKey.load_private().
    """
    self.public_key = public_key
    self.private_key = private_key

  @classmethod
  def new(self, bits=384, randomness=None):
    """ 
    Generates a new random HMAC key with the specified number of bits and
    returns it as a string, encoded per RFC4648 section 5 (base64 with the alternate,
    URL-safe, alphabet).
    """

    raise DataWireKeyUnimplementedError("Generating new RSA keys is not yet implemented.")

  @classmethod
  def load_private(path):
    """ 
    Load a RSA private key from a PEM-encoded file.

    NOTE WELL: That's a PEM-encoded RSA PRIVATE KEY (which, of course, has both private
    and public key information in it). Using an X.509 certificate WILL NOT WORK.
    """

    pem = open(path, "r").read()

    if not pem.startswith('-----BEGIN RSA PRIVATE KEY-----'):
      raise DataWireKeyBadFormatError("not a PEM-format RSA private key")

    return DataWireRSAKey(private_key=pem)

  @classmethod
  def load_public(path):
    """ 
    Load a RSA public key from a PEM-encoded file.

    NOTE WELL: That's a PEM-encoded PUBLIC KEY (which, of course, has no private
    key information in it). Using an X.509 certificate WILL NOT WORK.
    """

    pem = open(path, "r").read()

    if not pem.startswith('-----BEGIN PUBLIC KEY-----'):
      raise DataWireKeyBadFormatError("not a PEM-format RSA public key")

    return DataWireRSAKey(public_key=pem)

class DataWireKey (object):
  """
  Wrapper class. Right now, we use HMAC keys, which are of course symmetric,
  but we still implement the public/private entry points.
  """

  @classmethod
  def load_private(path, type='HMAC'):
    """
    Load an HMAC key from path

    Obviously HMAC keys are symmetric. This entry is here for compatibility with
    RS256 later.
    """

    if type != 'HMAC':
      raise DataWireKeyUnimplementedError("only HMAC keys are currently implemented")

    try:
      key = DataWireHMACKey.load(path)

      return DataWireResult.OK(privateKey=key.bits)
    except DataWireKeyError as e:
      return DataWireResult.fromError(e.message)

  @classmethod
  def load_public(path, type='HMAC'):
    """
    Load an HMAC key from path

    Obviously HMAC keys are symmetric. This entry is here for compatibility with
    RS256 later.
    """

    if type != 'HMAC':
      raise DataWireKeyUnimplementedError("only HMAC keys are currently implemented")

    try:
      key = DataWireHMACKey.load(path)

      return DataWireResult.OK(publicKey=key.bits)
    except DataWireKeyError as e:
      return DataWireResult.fromError(e.message)
