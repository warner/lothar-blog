Slug: Testing-SPAKE2-Interoperability
Date: 2017-06-04 09:22
Title: Testing SPAKE2 Interoperability
Category: cryptography

!BEGIN-SUMMARY!
I've been working on
a [Rust implementation](https://github.com/warner/spake2.rs) of SPAKE2.
I want it to be compatible with
my [Python version](https://github.com/warner/python-spake2). What do I
need to change? How can I write unit tests for interoperability?
!END-SUMMARY!

## Left As An Exercise For The Author

The
[SPAKE2 paper](http://www.di.ens.fr/~pointche/Documents/Papers/2005_rsa.pdf),
like most self-respecting academic publications, leaves out a lot of
details that would be necessary to build a specific implementation.
Authors get tenure points for inventing and analyzing new protocols, but
unfortunately not for the necessary engineering work of defining
data-serialization formats and providing test vectors.

If you want to actually implement the protocol, you must answer a number
of extra questions (listed below). To make it interoperate with others,
you must both use the same answers. For protocols that are "grown up"
enough, folks like the IETF will publish RFCs with those details. SPAKE2
is not there yet ([RFC8125](https://www.rfc-editor.org/rfc/rfc8125.txt)
defines some considerations, and the CFRG has recently started on
a [draft](https://datatracker.ietf.org/doc/draft-irtf-cfrg-spake2/)), so
lucky us, we're on the cutting edge. Inevitably, the first few
implementations will come up with their own (mutually-incompatible)
approaches, but eventually we can learn from each other and agree upon
something better.

## SPAKE2 Library API

The library API is pretty simple, and basically consists of two
functions. The initial function will accept the password (probably as a
bytestring, but maybe as unicode) and the identities of the two sides.
It's a nondeterministic function (since it must pick a random scalar),
so some languages will require passing in a source of randomness, but to
be safe, application code should not be required to deal with this. The
initial function returns two things: a message to be sent to the peer,
and a state object to be used later.

The outbound message should probably be a bytestring (making the
application responsible for encoding it in whatever way is needed for
the channel it will use). It will generally be of a fixed length for any
given group, but it may be easier to tell application authors to expect
a variable-length byte vector.

The state object could be an opaque in-memory struct, or something which
can be serialized for use in a later invocation of the same application.

Then there will be a (deterministic) finalization function, that accepts
both the state object and a message received by the peer, and emits the
shared key (as a fixed-length bytestring). The length of the shared key
is up to the library author, but it's typically 256 or 512 bits (since
it's the output of the transcript hash). Applications that need more key
material should derive it from the shared key with HKDF, outside the
scope of the SPAKE2 library.

## Protocol Definitions

The details that any given SPAKE2 implementation must define are:

* how to represent/encode the "identities" of each side
* how to represent/encode the password
* what group to use
* what generator to use
* what "arbitrary group elements" to use for M and N
* how to represent the group element that is sent to the other party
* how to parse+validate the group element received from the other party
* how to assemble the transcript
* how to hash the transcript into a key

If the library offers serialization of the state object, then it must
also define a way to serialize and parse scalars, but this is private to
the library, so it doesn't need to be part of the interoperability
specification. Scalar parsing would also be needed by any private
deterministic testing interface, described below.

### Identities

The paper describes each side as having an "identity", such as a
username or server name. The idea here is to prevent an attacker from
re-using messages of one protocol execution in some other context. If
Alice is intending to establish a session key with Server1, then her
message should not be suitable for a similar process with Server2.

The protocol needs bytestrings (to put into the hashed transcript, since
hashes need bytes). But it may be appropriate for the library to accept
unicode strings, which can internally be converted to UTF-8 through some
deterministic process. There are, unfortunately, multiple ways to
convert sufficiently weird unicode strings into UTF-8, but there's one
recommended canonical encoding ("NFC") that should work for all but the
strangest of inputs.

Options:

* bytestrings
* unicode strings, plus a specific encoding to use

### Password

The input password should be a bytestring. Any necessary encoding should
be done by the application before submitting a bytestring to the SPAKE2
library (if the application needs to allow humans to choose the
password, then it may want to accept unicode and perform UTF-8 encoding
itself). The same arguments for identities apply here, but I prefer to
make applications explicitly deal with the exciting possibilities that
unicode passwords offer you. In addition, it's entirely valid to have
the password be the output of some other hash function (maybe you
stretch it with [Argon2](https://www.argon2.com/) first), in which case
requiring a unicode string would be messy.

Internally, the password must be converted into a scalar of the chosen
group. This will be an integer from 0 to the group order (the order will
be some large prime number P, so the scalar will be meet the constraint
``0 <= pw_scalar < P``). This is typically performed by hashing the
password into enough bits to exceed the size of the order, treating
those bits as an integer, then taking the result ``mod P``.

```
def convert_password_to_scalar(password_bytes, P):
    assert (256/8) > (4*len("{:x}".format(P)))
    pw_hash_bytes = sha256(password_bytes).digest()
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
2 twice as often as any other scalar, which is a huge bias.

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

Fortunately we don't need any of this for PAKE: the password isn't
uniformly distributed anyways, so we don't require the scalar to be
uniform either. The main reason for using a hash is to accomodate
arbitrary-length passwords. 256 bits is more entropy than any
conceivable password, so using ``convert_password_to_scalar()`` from
above should be plenty.

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/groups.py#L70):
  HKDF(password, info="SPAKE2 pw", salt="", hash=SHA256), expand to
  32+16 bytes, treat as big-endian integer, modulo down to the Ed25519
  group order (2^252+stuff)

### The Group

Ed25519 is a nice choice for the group, but you could use others. My
python library defaults to Ed25519 but also implements a couple of
integer groups.

The choice of group will also dictate what generator to use for the
base-point scalarmult operation.

* What python-spake2 does: defaults to Ed25519, but offers
  1024/2048/3072-bit integer groups too.

### Arbitrary Group Elements: M and N

The M and N elements must be constructed in a way that prevents anyone
from knowing their discrete log. This generally means hashing some seed
and then converting the hash output into an element. For integer groups
this is pretty easy: just treat the bits as an integer, and then clamp
to the right range. For elliptic-curve groups, you treat the bits as a
compressed representation of a point (i.e. pretend the bits are the Y
coordinate, then recover the X coordinate), but you must make sure that
the point is correct too: it must be on the right curve (not the twist),
and it must be in the right subgroup.

Nominally, this only ever needs to be done once. I could copy the M and
N values from python-spake2 into spake2.rs (as a big hex string) and
include a note that says "if you want proof that these were generated
safely, go run python-spake2". But it'd be nice to be more transparent,
which may require porting the specific seed-to-arbitrary-element
algorithm into the new language too.

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/ed25519_basic.py#L271):
  HKDF(seed, info="SPAKE2 arbitrary element", salt=""), expand to 32+16
  bytes, treat as big-endian integer, modulo down to field order
  (2^255-19), treat as a Y coordinate, recover X coordinate, always use
  the "positive" X value, reject if (X,Y) is not on curve, multiply by
  cofactor to get candidate point, reject candidate is zero (i.e. we
  started with one of the 8 low-order points), reject if candidate times
  cofactor is zero (i.e. candidate was not in the right subgroup),
  return candidate. If the candidate is rejected, increment the Y
  coordinate by 1, wrap to field order, try again. Repeat until success.
  We expect this to loop 2*8=16 times on average before yielding a valid
  point.

### Element Representation and Parsing

Element representation is the most obvious compatibility-impacting
decision to make, as the algorithm provides a group element (e.g. a
point) for the first message, but the library API returns a bytestring.
So clearly we need to define how we turn group elements into bytes.

The X.509 certificate world has a fairly well-established process for
doing this, called BER or DER, and it includes things like multiple
compression mechanisms and built-in curve identifiers. The security
community has an equally well-established distaste for BER/DER, because
the parsers are hard to implement correctly (and without buffer
overflows), and these days flexibility is considered a misfeature.

For the Ed25519 group, points are represented as they are in the Ed25519
signature protocol: a 32-byte string, containing the Y coordinate as a
255-bit little-endian number, with the sign of the X coordinate appended
as the last bit.

On the receiving side, the library must parse the incoming bytes into a
group element. Obviously the encoder/parser pair must round-trip
correctly for anything generated by our library, but it must also work
*safely* for other random strings. There is some debate about the issue,
but for safety, the receiving side should reject any message which turns
into:

* a point that's not actually on the right curve
* a point that's not actually a member of the expected subgroup

The former is accomplished by testing the recovered X and Y coordinates
against the curve equation, which takes time. The latter is done by
multiplying by the order of the group (the details of which depend upon
the "cofactor"), and can take as much time as the main SPAKE2 math
itself (so potentially doubling the total CPU cost). However both are
important to do, and worth the slowdown.

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/ed25519_basic.py#L342):
  encode points like Ed25519 does, reject not-on-curve and
  not-in-correct-subgroup points during parsing.

### Transcript Generation

The penultimate step of SPAKE2 is to assemble everything we've sent and
received and computed into a sequence of bytes:

* the password
* the "identity strings" for both sides
* the messages that were exchanged
* the shared derived group element

The secrecy of the shared key comes entirely from that last element
(there are variations that don't include the password, but the proof is
stronger when it is included). However many early protocols, which did
not include the other values, were vulnerable to mix-and-match attacks
that combined portions of multiple conversations. Modern protocols
prevent this by building a "conversation transcript", which contains
every message that was exchanged (as well as the "inner voice" secrets
that are computed), and finally hashing the whole thing.

The concatenation scheme must resist "format confusion" attacks: where
the combination of (A1, B1) results in the same bytes as a combination
of some different (A2, B2). This only really happens when either value
can be variable-length, and the length is not correctly included in the
combined form. For example:

```
def unsafe_cat(a, b): return a+b
assert unsafe_cat("youlo", "se") != unsafe_cat("you", "lose")
```

Adding a fixed delimiter is unsafe if the strings could contain the
delimiter:

```
def unsafe_cat2(a, b): return a+":"+b
assert unsafe_cat("you:lo", "se") != unsafe_cat("you", "lo:se")
```

Escaping the delimiter can work, but is touchy. The safe way to do this
is to either prefix all variable-length strings with a fixed-size length
field, or to hash them and concatenate the fixed-length hashes.

```
def safe_cat(a, b):
    assert len(a) < 2**64
    assert len(b) < 2**64
    return struct.pack(">LsLs", len(a), a, len(b), b)
```

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/spake2.py#L45):
  transcript =
  sha256(password)+sha256(idA)+sha256(idB)+msg_A+msg_B+shared_element.to_bytes()

### Hashing the Transcript

Finally, the transcript bytes are hashed, and the result is used as the
shared key. The library must choose the hash function to use (SHA256 is
a fine choice), which nails down exactly how large the shared key will
be.

Hash functions can be specialized for specific purposes (the HKDF
"context" argument provides this, or the BLAKE2 "personalization"
string). This helps to ensure that hashes computed for one purpose won't
be confused with those used for some other purpose. For SPAKE2 this
doesn't seem likely, but a given library might choose to use a
personalization string that captures the other implementation-specific
choices that it makes.

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/spake2.py#L45):
  key = sha256(transcript)

## Testing Interoperability

The interactive nature of the protocol makes it particularly hard to
write unit tests of interoperability, especially the kind where you
compare a new execution transcript against a known "good" trace copied
earlier. If we could usefully replay a transcript of the interaction,
then it wouldn't be a zero-knowledge proof. To test two implementations
against each other non-interactively, we have to break both
implementations, by forcing them to use a known scalar, rather than a
unique random value.

This requires modifying the code. We can't exercise the random-scalar
part without interaction, but we can exercise everything beyond that
point. Implementations should be factored into two parts: an outer
function (called by application code) which generates a random scalar,
and an inner function which accepts the scalar as input and generates
the first message (and the state that's passed to the second half).


Testing would benefit from an online server that can perform protocol
queries (with fully random values), which will emit both the normal
protocol message *and* the normally-secret key. To help with debugging
mismatches, this test server should also reveal its internal state: the
secret scalar, and the full transcript. If your implementation gets a
different key, you can go back and compare the intermediate values until
you find the first one that doesn't match.

### TODO (blog draft)

* do we need to minimize bias in the password-to-scalar function?
* remove discussion about uniform password-to-scalar hashing?
* Element Representation: link "some debate about the issue" to the
  curves-list discussion
