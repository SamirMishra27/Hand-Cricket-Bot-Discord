"""
Excerpts of this code has been taken from the pycrptodome project on Github.
All the code here respectively belongs to their rightful project owners.
"""

def ceil_div(n, d):
    """Return ceil(n/d), that is, the smallest integer r such that r*d >= n"""

    if d == 0:
        raise ZeroDivisionError()
    if (n < 0) or (d < 0):
        raise ValueError("Non positive values")
    r, q = divmod(n, d)
    if (n != 0) and (q != 0):
        r += 1
    return r


def size (N):
    """Returns the size of the number N in bits."""

    if N < 0:
        raise ValueError("Size in bits only avialable for non-negative numbers")

    bits = 0
    while N >> bits:
        bits += 1
    return bits

import struct

def long_to_bytes(n, blocksize=0):
    """Convert an integer to a byte string.
    In Python 3.2+, use the native method instead::
        >>> n.to_bytes(blocksize, 'big')
    For instance::
        >>> n = 80
        >>> n.to_bytes(2, 'big')
        b'\x00P'
    If the optional :data:`blocksize` is provided and greater than zero,
    the byte string is padded with binary zeros (on the front) so that
    the total length of the output is a multiple of blocksize.
    If :data:`blocksize` is zero or not provided, the byte string will
    be of minimal length.
    """
    # after much testing, this algorithm was deemed to be the fastest
    s = b''
    n = int(n)
    pack = struct.pack
    while n > 0:
        s = pack('>I', n & 0xffffffff) + s
        n = n >> 32
    # strip off leading zeros
    for i in range(len(s)):
        if s[i] != b'\x00'[0]:
            break
    else:
        # only happens when n == 0
        s = b'\x00'
        i = 0
    s = s[i:]
    # add back some pad bytes.  this could be done more efficiently w.r.t. the
    # de-padding being done above, but sigh...
    if blocksize > 0 and len(s) % blocksize:
        s = (blocksize - len(s) % blocksize) * b'\x00' + s
    return s

def bytes_to_long(s):
    """Convert a byte string to a long integer (big endian).
    In Python 3.2+, use the native method instead::
        >>> int.from_bytes(s, 'big')
    For instance::
        >>> int.from_bytes(b'\x00P', 'big')
        80
    This is (essentially) the inverse of :func:`long_to_bytes`.
    """
    acc = 0

    unpack = struct.unpack

    # Up to Python 2.7.4, struct.unpack can't work with bytearrays nor
    # memoryviews
    #if sys.version_info[0:3] < (2, 7, 4):
    #    if isinstance(s, bytearray):
    #        s = bytes(s)
    #    elif isinstance(s, memoryview):
    #        s = s.tobytes()

    length = len(s)
    if length % 4:
        extra = (4 - length % 4)
        s = b'\x00' * extra + s
        length = length + extra
    for i in range(0, length, 4):
        acc = (acc << 32) + unpack('>I', s[i:i+4])[0]
    return acc

def is_native_int(x):
    return isinstance(x, int)


from os import urandom

class _UrandomRNG(object):

    def read(self, n):
        """Return a random byte string of the desired size."""
        return urandom(n)

    def flush(self):
        """Method provided for backward compatibility only."""
        pass

    def reinit(self):
        """Method provided for backward compatibility only."""
        pass

    def close(self):
        """Method provided for backward compatibility only."""
        pass
        

def new(*args, **kwargs):
    """Return a file-like object that outputs cryptographically random bytes."""
    return _UrandomRNG()


def atfork():
    pass


#: Function that returns a random byte string of the desired size.
get_random_bytes = urandom


class StrongRandom(object):
    def __init__(self, rng=None, randfunc=None):
        if randfunc is None and rng is None:
            self._randfunc = None
        elif randfunc is not None and rng is None:
            self._randfunc = randfunc
        elif randfunc is None and rng is not None:
            self._randfunc = rng.read
        else:
            raise ValueError("Cannot specify both 'rng' and 'randfunc'")

    def getrandbits(self, k):
        """Return an integer with k random bits."""

        if self._randfunc is None:
            self._randfunc = new().read #Random.new().read
        mask = (1 << k) - 1
        return mask & bytes_to_long(self._randfunc(ceil_div(k, 8)))

    def randrange(self, *args):
        """randrange([start,] stop[, step]):
        Return a randomly-selected element from range(start, stop, step)."""
        if len(args) == 3:
            (start, stop, step) = args
        elif len(args) == 2:
            (start, stop) = args
            step = 1
        elif len(args) == 1:
            (stop,) = args
            start = 0
            step = 1
        else:
            raise TypeError("randrange expected at most 3 arguments, got %d" % (len(args),))
        if (not is_native_int(start) or not is_native_int(stop) or not
                is_native_int(step)):
            raise TypeError("randrange requires integer arguments")
        if step == 0:
            raise ValueError("randrange step argument must not be zero")

        num_choices = ceil_div(stop - start, step)
        if num_choices < 0:
            num_choices = 0
        if num_choices < 1:
            raise ValueError("empty range for randrange(%r, %r, %r)" % (start, stop, step))

        # Pick a random number in the range of possible numbers
        r = num_choices
        while r >= num_choices:
            r = self.getrandbits(size(num_choices))

        return start + (step * r)

    def randint(self, a, b):
        """Return a random integer N such that a <= N <= b."""
        if not is_native_int(a) or not is_native_int(b):
            raise TypeError("randint requires integer arguments")
        N = self.randrange(a, b+1)
        assert a <= N <= b
        return N

    def choice(self, seq):
        """Return a random element from a (non-empty) sequence.
        If the seqence is empty, raises IndexError.
        """
        if len(seq) == 0:
            raise IndexError("empty sequence")
        return seq[self.randrange(len(seq))]

    def shuffle(self, x):
        """Shuffle the sequence in place."""
        # Fisher-Yates shuffle.  O(n)
        # See http://en.wikipedia.org/wiki/Fisher-Yates_shuffle
        # Working backwards from the end of the array, we choose a random item
        # from the remaining items until all items have been chosen.
        for i in range(len(x)-1, 0, -1):   # iterate from len(x)-1 downto 1
            j = self.randrange(0, i+1)      # choose random j such that 0 <= j <= i
            x[i], x[j] = x[j], x[i]         # exchange x[i] and x[j]

    def sample(self, population, k):
        """Return a k-length list of unique elements chosen from the population sequence."""

        num_choices = len(population)
        if k > num_choices:
            raise ValueError("sample larger than population")

        retval = []
        selected = {}  # we emulate a set using a dict here
        for i in range(k):
            r = None
            while r is None or r in selected:
                r = self.randrange(num_choices)
            retval.append(population[r])
            selected[r] = 1
        return retval

_r = StrongRandom()
getrandbits = _r.getrandbits
randrange = _r.randrange
randint = _r.randint
choice = _r.choice
shuffle = _r.shuffle
sample = _r.sample
