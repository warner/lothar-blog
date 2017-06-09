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

Anyone who wants to write one, and make it interoperate with other
people's implementations, needs to answer a number of extra questions
(listed below). For protocols that are actually used, folks like the
IETF will publish RFCs with the details. SPAKE2 is not there yet
([RFC8125](https://www.rfc-editor.org/rfc/rfc8125.txt) defines some
considerations, and the CFRG has recently started on
a [draft](https://datatracker.ietf.org/doc/draft-irtf-cfrg-spake2/)), so
we're on the cutting edge. The first few implementations will come up
with their own (mutually-incompatible) approaches, and then the next few
will try to match those or break away and do something better.

## SPAKE2 Library API

The library API is pretty fixed. There's going to be an initial function
that accepts the password (probably as a bytestring, but maybe as
unicode) and the identities of the two sides. It's a nondeterministic
function (since it must pick a random scalar), so some languages will
require passing in a source of randomness, but in general application
code should not be required to deal with this. The initial function
returns two things: a message to be sent to the peer, and a state object
to be used later.

The outbound message should probably be a bytestring (making the
application responsible for encoding it in whatever way is needed for
the channel it will use). It will generally be of a fixed length for any
given group, but it may be easier to tell application authors to expect
a variable-length byte vector.

The state object could be an opaque in-memory struct, or something which
can be serialized for use in a later invocation of the same application.

Then there will be a finalization function, that accepts both the state
object and a message received by the peer, and emits the shared key (as
a fixed-length bytestring). The length of the shared key is up to the
library author, but it's typically 256 or 512 bits (since it's the
output of the transcript hash). Applications that need more key material
should derive it from the shared key with HKDF.

## Protocol Definitions

The details that any given SPAKE2 implementation must define are:

* how to represent/encode the "identities" of each side
* how to represent/encode the password
* what group to use
* what generator to use
* what "arbitrary group elements" to use for M and N
* how to represent the group element that is sent to the other party
* how to parse+validate the group element received from the other party
* how to generate the transcript
* how to hash the transcript into a key

If the library offers serialization of the state object, then it must
also define a way to serialize and parse scalars, but this is private to
the library, so it doesn't need to be part of the interoperability
specification.

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

### Password

The input password should be a bytestring. Any necessary encoding should
be done by the application before submitting a bytestring to the SPAKE2
library (if the application needs to allow humans to choose the
password, then it may want to accept unicode and perform UTF-8 encoding
itself).

Internally, the password must be converted into a scalar of the chosen
group. This will be an integer from 0 to the group order (the order will
be some large prime number P, so the scalar will be meet the constraint
``0 <= pw_scalar < P``). This is typically performed by hashing the
password into enough bits to exceed the size of the order, treating
those bits as an integer, then taking the result ``mod P``.

```
assert (256/8) > (4*len("%x" % P))
pw_hash_bytes = sha256(u"password".encode("utf-8")).digest()
pw_hash_int = int(binascii.hexlify(pw_hash_bytes), 16)
pw_hash_scalar = pw_hash_int % P
```

In situations where we need to minimize bias (e.g. we need a very
uniform distribution of scalars in the given range), the practice of
e.g. the Ed25519 code is to use a hash that's at least 128 bits longer
than the order, which is enough to "spread out" the wraparound region
and reduce the bias to a small fraction of a bit.

```
assert (512/8) > (128 + 4*len("%x" % P))
pw_hash_bytes = sha512(u"password".encode("utf-8")).digest()
pw_hash_int = int(binascii.hexlify(pw_hash_bytes), 16)
pw_hash_scalar = pw_hash_int % P
```

However I *think* PAKE protocols don't need a uniform distribution,
since passwords aren't uniformly distributed anyways. So the main reason
for hashing is to accomodate arbitrary-length passwords.

### The Group

Ed25519 is a nice choice for the group, but you could use others. My
python library defaults to Ed25519 but also implements a couple of
integer groups.

The choice of group will also specify what generator to use for the
base-point scalarmult operation.

### Arbitrary Group Elements: M and N

The M and N elements must be constructed in a way that prevents anyone
from knowing their discrete log. This generally means hashing some seed
and then converting the hash output into an element. For integer groups
this is pretty easy: just treat the bits as an integer, and then clamp
to the right range. For elliptic-curve groups, you treat the bits as a
compressed representation of a point (i.e. pretend the bits are the X
coordinate, then recover the Y coordinate), but you must make sure that
the point is correct too: it must be on the right curve (not the twist),
and it must be in the right subgroup.

Nominally, this only ever needs to be done once. I could copy the M and
N values from python-spake2 into spake2.rs (as a big hex string) and
include a note that says "if you want proof that these were generated
safely, go run python-spake2". But it'd be nice to be more transparent,
which may require porting the specific seed-to-arbitrary-element
algorithm into the new language too.

### Element Representation and Parsing

Element representation is the most obvious compatibility-impacting
decision to make, as the algorithm provides a group element (e.g. a
point) for the first message, and library API returns a bytestring. So
we need to turn a group element into bits.

The X.509 certificate world has a fairly well-established process for
doing this, called BER or DER, and it includes things like multiple
compression mechanisms and built-in curve identifiers. BER/DER are
equally-well disliked by the security community, because parsers are
hard to implement correctly (and without buffer overflows), and these
days flexibility is considered a misfeature.

In the modern approach, if you really want a version string, then use
exactly one of them, at the top level, and have it dictate the type (and
representation) of everything inside.

For the Ed25519 group, points are represented as they are in the Ed25519
signature protocol: a 32-byte string, containing the X coordinate as a
256-bit little-endian number, with the sign of the Y coordinate in the
LSB.

On the receiving side, the library must translate the incoming bytes
into a group element. Obviously this must work correctly for anything
generated by the same library, but it must also work *safely* for other
random strings. There is some debate about the issue, but for safety,
the receiving side should reject any message which turns into:

* a point that's not actually on the right curve
* a point that's not actually a member of the expected subgroup

The former is accomplished by testing the recovered X and Y coordinates
against the curve equation, which takes time. The latter is done by
multiplying by the order of the group (the details of which depend upon
the "cofactor"), and can take as much time as the main SPAKE2 math
itself (so potentially doubling the total CPU cost). However both are
important to do, and worth the slowdown.

### Transcript Generation

The penultimate step of SPAKE2 is to assemble everything into a sequence
of bytes:

* password
* the "identity strings" for both sides
* the messages that were exchanged
* the shared derived group element

The secrecy of the shared key comes entirely from that last element.
However many early protocols, which did not include the other values,
were vulnerable to mix-and-match attacks that combined portions of
multiple conversations. These days, protocols compile a "conversation
transcript", which contains every message that was exchanged (as well as
the "inner voice" secrets that are computed), and hash the whole thing.

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



## Testing Interoperability

The interactive nature of the protocol makes it particularly hard to
write unit tests of interoperability. If we could usefully replay a
transcript of the interaction, then it wouldn't be a zero-knowledge
proof. To test two implementations against each other, we have to break
both implementations, by forcing them to use a known scalar, rather than
a unique random value.

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
