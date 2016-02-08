from __future__ import absolute_import

import base64
import json
import random as stdRandom

class DataWireRandom (object):
  # 34 because we use 0-9 A-Z, but we deliberately drop letters O and I
  base34chars = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
  bitsPerBase34Char = 5.08746284125034  # math.log(34) / math.log(2)

  def __init__(self):
    self.random = stdRandom.SystemRandom()

  def prettyJSON(self, obj):
    return json.dumps(obj, indent=4, separators=(',',':'), sort_keys=True)

  def randomBits(self, numBits):
    """
    Returns a integer containing numBits random bits.

    The only difference between this and randomBitString() is return type.
    """

    return self.random.getrandbits(numBits)

  def randomBitString(self, numBits):
    """
    Returns a string containing numBits random bits. numBits must be a multiple
    of 8.

    The only difference between this and randomBits() is return type.
    """

    if (numBits % 8) != 0:
      raise ValueError("DataWireRandom.randomBitString can only generate multiples of 8 bits")

    # We're building e.g. %02X for 8 bits, %04X for 16... always numBits / 4.
    fmtString = "%%0%dX" % (numBits / 4)

    bitString = (fmtString % self.randomBits(numBits)).decode("hex")

    return bitString

  def randomBase34String(self, numChars=10):
    # Round down here 'cause WTF, just a bit.
    numBits = int(numChars * DataWireRandom.bitsPerBase34Char)

    return self.toBase34(self.randomBits(numBits), numChars)

  def toBase34(self, value, numChars):
    # Do this the lazy way, which means reversing our bits basically. Who cares?

    output = []

    for i in range(numChars):
      output.append(DataWireRandom.base34chars[value % 34])
      value //= 34

    return "".join(output)

  def randomID(self):
    """ 
    An ID here is a ten-digit base-34 string (A-Z0-9, but discarding O and I).
    That means 34^10 combinations == 50.87 bits, so we'll grab 50 bits and call
    it good.

    (Could this be better? Sure. Gotta start somewhere though.)
    """

    return self.randomBase34String()

  def randomPassword(self):
    return self.randomBase34String(40)
