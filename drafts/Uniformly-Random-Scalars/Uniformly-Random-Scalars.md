Slug: Uniformly-Random-Scalars
Date: 2017-07-15 21:13
Title: Uniformly Random Scalars

!BEGIN-SUMMARY!
Many cryptographic protocols, like Diffie-Hellman and SPAKE2, require a
way to choose a uniformly random scalar from some prime-order range.
Why? What is the best way to do this?
!END-SUMMARY!

Classic Diffie-Hellman Key Exchange (which, to be picky, is really Key
Agreement) starts with each side chosing a random scalar. This 


The password is needed in two places. The first (and most complicated)
one is as a scalar in the chosen group, where it is used to blind the
public Diffie-Hellman parameters. The second is when it gets copied into
the transcript (see below).

For the first case, the password must be converted into a scalar of the
chosen group (this is enough of a nuisance that PAKE papers like to
pretend that users have integers as passwords rather than strings). This
will be an integer from 0 to the group order (the order will be some
large prime number P, so the scalar will be meet the constraint ``0 <=
pw_scalar < P``). This is typically performed by hashing the password
into enough bits to exceed the size of the order, treating those bits as
an integer, then taking the result ``mod P``.

```
def convert_password_to_scalar(password_bytes, P):
    pw_hash_bytes = sha256(password_bytes).digest()
    # double-check that our hash function produces a big enough integer
    assert len(pw_hash_bytes) > (4*len("{:x}".format(P)))
    pw_hash_int = int(binascii.hexlify(pw_hash_bytes), 16)
    pw_hash_scalar = pw_hash_int % P
    return pw_hash_scalar
```

Since the order is always prime, and the hash output is always an
integral number of bits, the mapping will never be exactly uniform. Some
protocols are weakened by non-uniform scalars (such as the random ``k``
nonce in non-deterministic ECDSA), so you may need to minimize the bias
imposed by the case where your hash integer is larger than P. For
example, if P=13, and you use a 4-bit hash, then you'll get a 0 or 1 or
2 twice as often as any other scalar, which is a huge bias. So you'll
see some crypto libraries try to reduce this bias.

The "try-try-again" fix, which I used
in [python-ecdsa](https://github.com/warner/python-ecdsa), is to skip
the ``%P``, include a counter in the hash input, and keep incrementing
the counter until the hash output integer just so happens to be in the
right range. This takes an unpredictable amount of time (although on
average you only have to try twice, if you truncate the hash output
right), but provides a perfectly uniform output.

Unbounded runtime is a drag, so the practice of e.g. the Ed25519 code is
to use a hash that's at least 128 bits longer than the order, which is
enough to "spread out" the wraparound region and reduce the bias to a
small fraction of a bit.

```
# conversion that reduces the bias to a fraction of a bit
assert (512/8) > (128 + 4*len("%x" % P))
pw_hash_bytes = sha512(u"password".encode("utf-8")).digest()
pw_hash_int = int(binascii.hexlify(pw_hash_bytes), 16)
pw_hash_scalar = pw_hash_int % P
```

Fortunately we don't need any of this for PAKE protocols (neither SPAKE2
nor other members of the family): the password isn't uniformly
distributed anyways, so we don't require the scalar to be uniform
either. The main reason for using a hash is to accomodate
arbitrary-length passwords. 256 bits is more entropy than any
conceivable password, so using ``convert_password_to_scalar()`` from
above should be plenty.

Both sides must perform this conversion in exactly the same way,
otherwise they'll get mismatched keys. All aspects must be the same: the
overall algorithm, the hash function you use, the way the hash output is
turned into an integer (big-endian vs little-endian will trip you up),
and the final modulo operation.

Also note that, while scalars are "really" just integers, many crypto
libraries (even ones written in languages like Python with built-in
"bigint" support) do not represent them that way. Instead they may be
stored in an opaque binary array, to make the math faster.

When I wrote python-spake2, I was (incorrectly) worried about
uniformity, so I used an overly complicated approach. If I were to start
again, I'd use something simpler.

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/groups.py#L70):
  HKDF(password, info="SPAKE2 pw", salt="", hash=SHA256), expand to
  32+16 bytes, treat as big-endian integer, modulo down to the Ed25519
  group order (2^252+stuff)
* What draft-irtf-crfg-spake2-03 does: left as an exercise, although
  key-stretching is recommended
  
Note that key-stretching only matters if the same password is used for
multiple executions of the protocol. Stretching would be most useful on
a login system using the SPAKE2+ variant. In SPAKE2+, the "server" side
stores a derivative of the password, so a server compromise does not
immediately allow client impersonation: this password derivative must
first be brute-forced to reveal the original password, and each loop of
this process will be lengthened by the stretch. In magic-wormhole, a new
wormhole code is generated each time, and nothing is stored anywhere, so
stretching is not necessary.


### Arbitrary Group Elements: M and N

The M and N elements must be constructed in a way that
[prevents anyone from knowing their discrete log](http://www.lothar.com/blog/54-spake2-random-elements/).
This generally means hashing some seed and then converting the hash
output into an element. For integer groups this is pretty easy: just
treat the bits as an integer, and then clamp to the right range. For
elliptic-curve groups, you treat the bits as a compressed representation
of a point (i.e. pretend the bits are the Y coordinate, then recover the
X coordinate), but you must make sure that the point is correct too: it
must be on the correct curve (not the twist), and it must be in the
correct subgroup.

Why hash a string? We definitely want different values for M and N, we
kind of want different values for different curves, and it would be cool
to reduce our ability to fiddle with the results too much: the elements
we pick should somehow be the most "obvious" choice. Another name for
this property is the "nothing up my sleeve" number. djb's
[bada55](https://bada55.cr.yp.to/) site (and the delightfully amusing
[paper](https://bada55.cr.yp.to/bada55-20150927.pdf)) touch on this.
Pretend that we're trying to build a sabotaged standard, defined to use
an element for which we (and we alone) know a discrete log. Maybe we
have some magic way to learn the discrete log of, say, one in every
million elements. And say that instead of a seed, we're just using an
integer. Now we could just keep trying sequential integers until we get
an element that we can DLOG, and then we write this not-huge integer
into our standard, and tell folks something like "oh, 31337 was my first
phone number, so that was the most obvious choice", muahaha.

Using a short seed, named something obvious like "M", gives us a warm
fuzzy feeling that there's not much wiggle room to perform this
hypothetical search for a bad element. It's not perfect, though, since
we can probably just wiggle the other aspects (which hash to use, which
other fields to include in the hash, the order to arrange them, etc). So
hash-small-seed is nominally a good idea, but the real safety comes from
the choice of group and the hardness of the DLOG assumption.

Using a string seed that includes the curve name means we'll definitely
get different (and quite unrelated) values for different curves, but to
be honest using different curves pretty much gives you that anyways, and
it's not clear how similar-looking elements in unrelated curves could be
used as an attack anyways. The general concern is that you might use the
same password on two different instances of the protocol (one with each
curve), and then an attacker can somehow exploit confusion about which
messages go with which curve.

So that's how get a "safe" element. Nominally, this only ever needs to
be done once: in theory, I could publish the program that turns a seed
of "M" into 0x19581b8f3.. in a blog post, and then just copy the big hex
values into python-spake2, and include a note that says "if you want
proof that these were generated safely, go run the program from my blog.
And if you actually went and downloaded that code and ran it and
compared the strings, then you'd get the same level of safety. But
nobody will actually do that, so we can inspire more confidence by
adding the seed-to-element code into the library itself, and starting
from a seed instead of a big hex string.

Since we need all implementations to use the same M/N elements, this
means we may need to port the specific seed-to-arbitrary-element routine
from the original language (where maybe it was a pretty natural
algorithm) into each target language (where it may seem
overcomplicated).

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/ed25519_basic.py#L271):
  HKDF(seed, info="SPAKE2 arbitrary element", salt=""), with seed equal
  to "M" or "N", expand to 32+16 bytes, treat as big-endian integer,
  modulo down to field order (2^255-19), treat as a Y coordinate,
  recover X coordinate, always use the "positive" X value, reject if
  (X,Y) is not on curve, multiply by cofactor to get candidate point,
  reject candidate is zero (i.e. we started with one of the 8 low-order
  points), reject if candidate times cofactor is zero (i.e. candidate
  was not in the right subgroup), return candidate. If the candidate is
  rejected, increment the Y coordinate by 1, wrap to field order, try
  again. Repeat until success. We expect this to loop 2*8=16 times on
  average before yielding a valid point. This happens at module import
  time.
* Symmetric Mode: a group element named S is constructed in the same
  way, with a seed of ``S``, and is used for blinding/unblinding in both
  directions (where SPAKE2 says "N", replace it with S, and where SPAKE2
  says "M", also replace it with S).
* What draft-irtf-crfg-spake2-03 does: find the OID for the curve,
  generate an infinite series of bytes (start with SHA256("$OID point
  generation seed (M)") for that OID to get the first 32 bytes, then
  SHA256(first 32 bytes) to get the second 32 bytes, repeat), slice into
  encoded-element lengths, clamp bits as necessary, interpret as point,
  if that fails repeat with the next slice. Do the same with "(N)".





Change 'Title', but 'Slug' must match the directory name for images to work
Markdown cheatsheet

![alt-text](./IMG_6722.jpg "tooltip/popup text")

## H2
### H3

* list1
  more of list1
* list2

   * sublist2.1 (needs intervening newline to end list2) (doesn't work)
   * sublist2.2

*italic* **bold**

--strikethrough-- (doesn't work)

links have [text](url "title")

```python
a = 'syntax highlighting' if True else 'not'
```

> blockquotes
> on multiple lines
