Slug: Uniformly-Random-Scalars
Date: 2017-07-15 21:13
Title: Uniformly Random Scalars

!BEGIN-SUMMARY!
Many cryptographic protocols, like Diffie-Hellman and SPAKE2, require a
way to choose a uniformly random scalar from some prime-order range.
Why? What is the best way to do this?
!END-SUMMARY!

## What (is a scalar)?

Classic
[Diffie-Hellman Key Exchange](https://en.wikipedia.org/wiki/Diffie_hellman)
starts with each side chosing a random scalar. This is kept secret, but
is used to derive a "public ephemeral element" that is sent to the other
side. It is also used upon the peer's ephemeral element to build the
shared secret element, from which the final secret key is derived.
SPAKE2, as a modified DH protocol, relies on this secret random scalar
too.

Scalars are basically integers in a specific range, bounded by the order
of an Abelian group, and the order is generally a big prime number P. To
be precise, scalars are "equivalence classes of integers modulo P",
meaning that you're choosing a *class* of integers, all of which are
equal to each other if your idea of "equal" is modulo P. If P is 5, then
one such equivalence class is the integers 2, 7, 12, -3, -8, -13, etc.
Each of these classes can be *represented* by a single member, which is
an integer between 0 and P, so we usually pretend that scalars are just
integers with the constraint that ``0 <= x < P``. We say "2" instead of
"the class that includes 2, 7, 12, etc".

Also note: there is some confusion, at least in my mind, about the
precise range of scalars. Some references (including the original SPAKE2
paper) say ``Zp``, which means any positive integer less than P (``0 <=
x < P``).
The [Handbook of Applied Cryptography](http://cacr.uwaterloo.ca/hac/)
section on Diffie-Hellman (protocol 12.47, page 516) says scalars should
be ``1 <= x <= P-2`` (excluding both 0 and -1). I'm pretty sure that 0
is a bad choice: in DH it will cause the resulting shared element to
always be the same thing (the identity element), independent of the
other party's message. It's a bit like
a [weak key](https://en.wikipedia.org/wiki/Weak_key) in symmetric
ciphers. But P is huge, so the chance of accidentally getting a scalar
of 0 (or any other specific value) is effectively nil. As long as the
protocol only uses scalars from trusted sources (i.e. ourselves, not the
network), we don't need to worry about it.

So for simplicity, I'll define our task to be generating an integer
``x``, where ``0 <= x < P`` for some large (prime) P, such that the
value is uniformly randomly distributed in that range (all values are
equally likely).

## Why (do we need a random one)?

The DSA and ECDSA signature algorithms also use a unique secret random scalar
(known as a "nonce", or just ``k``), and
[are vulnerable](https://crypto.stackexchange.com/questions/44644/how-does-the-biased-k-attack-on-ecdsa-work) to
attack if this nonce is biased. If you know the first or last few bits of
each nonce, and you have multiple signatures to work with, then a brute-force
search for the signer's private key is *much* easier than it should be. In
some cases, the private key can be recovered in a couple of hours.

Of course, if the implementation
[doesn't even try to be random](https://www.xkcd.com/221/), then you wind
up with things like the
[Playstation 3](https://arstechnica.com/gaming/2010/12/ps3-hacked-through-poor-implementation-of-cryptography/)
where they used the same hard-coded value of ``k`` for every single message,
allowing the private key to be recovered trivially with just two signatures.

It isn't clear if other protocols (like DH) are quite this vulnerable.
[The Logjam paper](https://weakdh.org/imperfect-forward-secrecy-ccs15.pdf),
in section 3.5, mentions attacks on small-exponent DH in poorly-chosen
integer groups, and this
[email about Curve25519 scalars](https://www.ietf.org/mail-archive/web/cfrg/current/msg05004.html)
points out the attack-resistance provided by their specific clamping
decisions (which constrain the scalar to certain values). But in
general, our security proofs are built around the assumption that the
scalar is unique and uniformly random, so to be safe we must follow
those rules.

## How (do we create one)?

We can assume that our operating system gives us a source of random
bytes. ``/dev/urandom`` on a fully-initialized unix-like host will give
us as many as we need.

If our target range ``0 <= x < 256``, or ``0 <= x < 65536``, or some other
power of 256, that'd be trivial. It would also be easy to produce integers in
a range that's any integral power of two (you just mask off the extra bits,
and treat the result as an integer). But since P is a prime, we're never
going to have a nice round size for truncation.

So we need to use ``/dev/urandom`` to get a **seed**, and then convert some
number of these seed bytes to an integer. This is pretty easy: just treat the
array of bytes as a base-256 number. In Python2, we can exploit the
``hexlify()`` and ``int()`` functions to make this really fast (python3 adds
``int.from_bytes()``, which is even better):

```
def bytes_to_integer(seed_bytes):
    return int(binascii.hexlify(seed_bytes), 16)
```

What's the range of this number? It will be 0 to ``2**len(seed_bytes)``.
If we use too few bytes, then it will obviously not even cover the
entire target range, so our first step is to make the seed larger than
the total range. This introduces the possibility of getting a number
that's too big, so we'll have to modulo down:

```
def make_random_scalar_with_bytes(seed_length_bytes, P):
    # check that our seed will produce sufficiently-large integers
    # the right-hand side is roughly equal to ln2(P)
    assert 8*seed_length_bytes > (4*len("{:x}".format(P)))
    seed_bytes = os.urandom(seed_length_bytes)
    hash_int = bytes_to_integer(seed_bytes)
    scalar = hash_int % P
    return scalar
```

What's a reasonable choice of seed length? For the Curve25519 group, P is
``2**252 + 27742317777372353535851937790883648493``, which lies on the low
end of the range between ``2**252`` and ``2**253``. If we use 253 random bits
(which you get from 32 random bytes by doing something like ``seed_bytes[0]
&= 0x1F`` to mask out the top three bits), then we'll get a suitable value
slightly more than half the time, and the modulo function will kick in (i.e.
"aliasing" occurs) slightly less than half the time.

But that's pretty badly biased. Each time aliasing happens (e.g.
``hash_int >= P``) means that two values of ``hash_int`` (which *is*
uniform) are mapping to the same value of ``scalar`` (which therefore is
not uniform). Consider the simple case of ``P = 2**8 - 1 == 255`` (so we
want outputs from 0 to 254, inclusive, and exclude only 255), and our
``seed_length`` is 1 byte. Seeds of 0 and 255 will both map to an output
of 0, so zeros will appear in the output twice as frequently as any
other value. The one case of aliasing will induce a bias in our output.

The amount of bias, in a statistical sense, depends upon how many extra
bits we start with, and how close our target ``P`` is to a power of 2,
so it's something like ``ln2(P) - floor(ln2(P))``, using the base-2
logarithm of our target P.

## The Best Good-Enough Solution

The simplest solution that yields a minimal bias is to throw more bits
at the problem. Using a ``seed_length`` that's 32 bytes (128 bits)
larger than we really need reduces the bias to a statistically
insignificant level. In this case, we're aliasing almost **all** the
time:

```
def make_random_scalar(P):
    # conversion that reduces the bias to a fraction of a bit
    minimal_length_bits = 4*len("%x" % P)
    safe_length_bits = minimal_length_bits + 128
    safe_length_bytes = safe_length_bytes // 8
    # that gets us between 121 and 128 bits of safety margin
    return make_random_scalar_with_bytes(safe_length_bytes, P)
```

This is the approach used by the Ed25519 codebase to compute unbiased
deterministic nonces from the private key and the message being signed.
These nonces have the same requirements as ECDSA: they must be unique
and unbiased. The Ed25519 signing function creates a 512-bit hash and
then reduces it down to the ~252-bit group order: see the bottom of page
6 of the [Ed25519 paper](http://ed25519.cr.yp.to/ed25519-20110926.pdf),
where ``r`` is the nonce, and computations end up being performed mod
``P`` (which they call ``l``). They use about 258 extra bits.

[FIPS 186-4](http://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf),
which defines DSA and ECDSA, says that 64 extra bits are sufficient (in
appendix B.2.1).

## The Exact Solution: Try-Try-Again

There is a way to remove **all** the bias, but you might not like it. To
achieve zero bias, you remove the modulo-P step (so there's no chance of
aliasing), and you add a loop that keeps trying new random seeds over
and over again until the integer just happens to be in the right range.

```
def try_try_again(P):
    length_in_bits = 4*len("%x" % P)
    seed_length_bytes = round_up_to_multiple_of_eight(length_in_bits)
    while True:
        seed_bytes = mask(os.urandom(seed_length_bytes), length_in_bits)
        candidate = bytes_to_integer(seed_bytes)
        if candidate < P:
            return candidate
        # else, try again
```

This takes an unpredictable amount of time, but provides a perfectly
uniform output. The number of trials that you'll need depends upon the
same bias that we're removing. If you mask the bytes down to the minimum
number of bits, then the worst case (where P is just slightly larger
than some power of 2) is an average of two passes. If you don't bother
masking individual bits, then the worst case is 255 average passes. If P
is just slightly **smaller** than a power of 2, the average is a single
pass.

But this is an exponential distribution: if you're really unlucky, it
could take thousands of iterations before you find a suitable integer,
or worse. The **mean** is small, but the **maximum** is infinite.

I used this "try-try-again" algorithm as an option in
[python-ecdsa](https://github.com/warner/python-ecdsa). But unbounded
runtime is a drag, so the recommended approach is to use the
extra-128-bits scheme described above (in ``make_random_scalar()``).

This technique is also used (since around 2003 for large ranges, and
[since 2010](https://bugs.python.org/issue9025) for all ranges) in
Python's ``random.SystemRandom.randrange()`` function, and
``secrets.randbelow()`` in Python3.6.

Before that point, python2.4 had
a [bug](http://bugs.python.org/issue812202) (reported by none other than
Ron Rivest, the R in RSA!) in which ``random.SystemRandom`` used
``/dev/urandom`` as a seed correctly, but ``randrange()`` used that seed
to create a floating point number, then multiplied it out to the desired
range (and rounded the result to an integer). As a result, no matter how
large a range you asked for, the number could never have more than about
53 bits of entropy (and in fact the low-order bits were always zero,
which is exactly where ECDSA is vulnerable).

That bug was fresh in my mind when I wrote the python-ecdsa code, which
is why I avoided using the standard library functions. But at this point
it's probably safe to just use the following (though be sure to check
what the underlying functions are really doing, especially if you're
porting this to some other language which might have made the same
mistake as Python):

```
import secrets
def make_random_scalar(P):
    return secrets.randbelow(P)
```

or, on python2.7:

```
from random import SystemRandom
def make_random_scalar(P):
    return SystemRandom().randrange(P)
```

## Scalars From Seeds

For testing, it may be useful to break the function up into two pieces.
The private inner function is deterministic, and accepts the seed bytes
as an argument. The externally-visible outer function is where
``/dev/urandom`` is sampled. The inner function can be unit tested.

```
def _bytes_to_integer(seed_bytes):
    return int(binascii.hexlify(seed_bytes), 16)
def _map_bytes_to_scalar(seed_bytes, P):
    # check that our seed will produce sufficiently-large integers
    # the right-hand side is roughly equal to ln2(P)
    assert 8*len(seed_bytes) > (4*len("{:x}".format(P)))
    hash_int = _bytes_to_integer(seed_bytes)
    scalar = hash_int % P
    return scalar
def make_random_scalar(P):
    # conversion that reduces the bias to a fraction of a bit
    minimal_length_bits = 4*len("%x" % P)
    safe_length_bits = minimal_length_bits + 128
    safe_length_bytes = safe_length_bytes // 8
    # that gets us between 121 and 128 bits of safety margin
    seed_bytes = os.urandom(seed_length_bytes)
    return _map_bytes_to_scalar(seed_bytes, P)
```

This can also be used in a related function: mapping seeds to scalars.
This function is needed for protocols like SPAKE2, where the
``password`` input must be converted into a scalar for the blinding
step. In this case, uniformity is not strictly necessary (the SPAKE2
password isn't randomly distributed, so any deterministic function of it
will have the same non-random distribution). But if your library already
has ``_map_bytes_to_scalar()``, then it may be easiest to build on top
of that:

```
def password_to_scalar(pw, P):
    seed = sha256(pw).digest()
    return _map_bytes_to_scalar(seed, P)
```

In addition, you might want the seed-to-scalar function to behave
differently for different protocols, so the same password used in two
different places doesn't produce values which could be mixed/matched in
an attack. The usual way to accomplish this is to feed some sort of
algorithm identifier into the hash function. Some options are:

* a simple prefix string:  ``sha256("my algorithm name" + pw)``
* a real key-derivation function: ``HKDF(context="my algorithm name",
  secret=pw)``. This also gives you exact control over the number of
  bytes, not limited to the native output size of the hash function.
* some modern hash functions like BLAKE2 have dedicated
  "personalization" inputs: ``blake2(input=pw, personalize="my algorithm
  name")``

## Use in python-spake2

All of this is an attempt to explain why the password-to-scalar function
in my [python-spake2](https://github.com/warner/python-spake2) library
is so over-complicated. When I wrote that function, I was worried that
the blinding scalar needed to be uniformly random (like most other
scalars in cryptographic protocols). So I combined all the techniques
above: both algorithm-specific hash personalization *and* using an
oversized hash output.

In retrospect, it would probably have been ok to just truncate a plain
SHA256 output to something less than the Curve25519 group order. In
fact, just using 128 bits would have been enough, which removes the need
for the modulo step.

```
def password_to_scalar(pw, P):
    return _bytes_to_integer(sha256(pw).digest()[:16])
```

So if you're looking at the ``password_to_scalar``
[function](https://github.com/warner/python-spake2/blob/master/src/spake2/groups.py#L70)
in [python-spake2](https://github.com/warner/python-spake2) and think
it's unnecessarily complicated, that's why.

## Conclusions

Thanks to Thomas Ptáček, Sean Devlin, Thomas Pornin, and Zaki Manian for
their advice and feedback.
