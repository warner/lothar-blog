Slug: Testing-SPAKE2-Interoperability
Date: 2017-06-04 09:22
Title: Testing SPAKE2 Interoperability
Category: cryptography

!BEGIN-SUMMARY!

I've been working on
a [Rust implementation](https://github.com/warner/spake2.rs) of SPAKE2.
I want it to be compatible with
my [Python version](https://github.com/warner/python-spake2). What do I
need to change? Where have I accidentally indulged in protocol design,
so a choice I make in this library might cause it to behave differently
than somebody else's library? How can I write unit tests for
interoperability?

!END-SUMMARY!

This post walks through the parts of the SPAKE2 protocol that a library
author must decide for themselves how to implement, most of which have a
direct bearing on potential compatibility with other libraries. It
describes the choices I happened to make while writing python-spake2,
none of which are necessarily the best, effectively (but accidentally)
defining a specification of sorts.

## Left As An Exercise For The Author

The
[SPAKE2 paper](http://www.di.ens.fr/~pointche/Documents/Papers/2005_rsa.pdf),
like most self-respecting academic publications, leaves out a lot of
details that would be necessary to build a specific implementation.
Authors get tenure points for inventing new protocols and breaking
existing ones, but unfortunately not for the necessary engineering work
of defining test vectors and data-serialization formats.

If you want to actually implement the protocol, you must answer a number
of extra questions (listed below). To make it interoperate with others,
you must both use the same answers. For protocols that are "grown up"
enough, folks like the IETF will publish RFCs with those details. SPAKE2
is not there yet ([RFC8125](https://www.rfc-editor.org/rfc/rfc8125.txt)
defines some considerations, and the CFRG has an
[expired draft](https://datatracker.ietf.org/doc/draft-irtf-cfrg-spake2/)),
so lucky us, we're on the cutting edge! The first few implementations
might choose mutually-incompatible approaches, but eventually we can
learn from each other and agree upon something interoperable.

The 0.7 release of my python-spake2 library incorporates some decisions
we made on
[pull request #273](https://github.com/bitwiseshiftleft/sjcl/pull/273)
of the [SJCL Project](https://github.com/bitwiseshiftleft/sjcl/) (a
pure-javascript crypto library), where we were able to hash out a
mostly-interoperable pair of libraries (python and JS). Some of the
discussions there may be useful. Jonathan Lange and JP Calderone are
working on [haskell-spake2](https://github.com/jml/haskell-spake2) and
are aiming for compatibility with python-spake2.


## SPAKE2 Overview

SPAKE2 belongs to a family of protocols named PAKE, which stands for
Password-Authenticated Key Exchange.

The SPAKE2 protocol lets Alice and Bob exchange messages (one each), and
then both sides calculate a secret key. If Alice and Bob used the same
password, their keys will be the same, and nobody else will know what
that key is.

You can imagine that Alice gives the password (and some other
identifying data) to her friendly local SPAKE2 Robot, which she bought
off the shelf at SPAKE2 Robots R' Us. The robot gives her a message to
deliver to Bob's robot. Meanwhile Bob is doing almost exactly the same
thing. When Alice gives Bob's message to her local robot, her robot
prints out a random-looking key. At the same time, Bob gives Alice's
message to his robot, and his robot prints out (hopefully) the same key.

Both Alice and Bob have to tell their robots that the first person
playing this game is named "Alice", and the second person is named
"Bob". They must also tell their robots who is who: Alice must say
"Robot, I'm the first person, not the second", and Bob must say "I'm the
second person, not the first". That last item, the "side", is the only
thing which they do differently.

Internally, these robots are going to generate some random numbers, do
some math, generate a message, accept a message, do some more math,
assemble a record of everything they've done and seen and thought into a
**transcript**, and then turn the transcript into a key. Part of the
transcript will be secret, which is what makes the key secret too.

## Your SPAKE2 Library API

The first thing to define is your local library API (the "SPAKE2
Robot"). This isn't completely exposed externally, of course: different
libraries with different APIs (in different languages) should be able to
interoperate if they can agree on all the other decisions we'll explore
below. But you don't have complete freedom either: some constraints
bleed through. We must glue together local API requirements, the wire
format, and the SPAKE2 math itself.

We'll consider some **application** that sits above the **library**.
You, as the library author, are providing an API to those applications.
You don't know what they need SPAKE2 for, or how they're going to use
it, but your job is to enable:

* safety: give the application author a decent chance of getting things
  right
* interoperability: enable compatibly-written applications (perhaps
  using different libraries, in other langauges) get the right results
  when run against an application using your library

The library API we need to provide is pretty simple, and basically
consists of two functions (but which could be expressed in different
ways):

``` python
(msg1, state) = start(password, idA, idB, side)
# somehow send msg1 to the other party
# somehow receive msg2 from the other party
key = finish(msg2, state)
# do something with the shared key
```

``start()`` will accept the password (probably as a bytestring, but
maybe as unicode), the identities of the two sides, and some way to
indicate which side this instance is playing. It's a nondeterministic
function (since it must pick a random scalar), so some languages will
require passing in a source of randomness, but to be safe, application
code should not be required to deal with this. The first function
returns two things: an outbound message to be sent to the peer, and a
state object to be used later.

``finish()`` is deterministic. It accepts both the state object and a
message received by the peer, and emits the shared key (as a
fixed-length bytestring). The length of the shared key is up to the
library author, but it's typically 256 or 512 bits (since it's the
output of the transcript hash). Applications that need more key material
should derive it from the shared key with HKDF, outside the scope of the
SPAKE2 library.

(You run both halves of the API on both sides. Each side will generate
one message and accept one message. Two messages are generated in all.)

The outbound message will be a bytestring, and the application will be
responsible for encoding it in whatever way is needed for the channel
(e.g. the app might need to base64-encode it to put into an HTTP header,
but that's outside the scope of the SPAKE2 library). It will generally
be of a fixed length for any given group (see below), but it may be
easier to tell application authors to expect a variable-length byte
vector.

The state object could be an opaque in-memory struct. For example, in
object-oriented languages, the first function may be an object
constructor, and the second is just a method call on that same object.
If the object can be serialized, or if the first function returns a
serializeable state object, then the application may be able to shut
down and be resumed in between the generation of the first message and
the receipt of the second (so the two users don't have to be online at
the same time). If you offer serialization, make sure to warn authors
against using the same state object twice, since this will hurt
security.

For two different libraries to interoperate, they must use the same key
length. They must also encode the same password in the same way, as well
as the identities of the two sides.

The application author's responsibilities are:

* give their user a way to enter a password
* deliver that password to your library (the first function)
* take the message your library returns and deliver it correctly to some
  remote application
* take the matching inbound message from the remote application and
  deliver it correctly to your library's second function
* do something useful with the shared key

### Symmetric Mode

My python-spake2 library also offers a "Symmetric Mode" which isn't
defined by the Abdalla/Pointcheval paper. This is a variant that I
developed, with help from Mike Hamburg and other crypto folks. It
removes the "side" parameter from the API, so two identical clients can
establish a key without pre-arranged knowledge of which one is which.

## Protocol Definitions

The details that any given SPAKE2 implementation must define are:

* how to represent/encode the "identities" of each side
* what group to use
* what generator element to use
* how to represent/encode the password, both as a scalar and in the
  transcript
* what "arbitrary group elements" to use for M and N (and S)
* how to encode the group element that is sent to the other party
* how to decode+validate the group element received from the other party
* how to assemble the transcript
* how to hash the transcript into a key

If the library offers serialization of the state object, then it must
also define a way to serialize and parse scalars, but this is private to
the library, so it doesn't need to be part of the interoperability
specification. Scalar parsing would also be needed by any private
deterministic testing interface, described below.

### Identities

[The paper](http://www.di.ens.fr/~pointche/Documents/Papers/2005_rsa.pdf)
describes each side as having an "identity", such as a username or
server name. The idea here is to prevent an attacker from re-using
messages of one protocol execution in some other context. If Alice is
intending to establish a session key with Server1, then her message
should not be suitable for a similar process with Server2.

The protocol needs bytestrings (to put into the hashed transcript, since
hashes need bytes), so the library API should require bytestrings. 

The canonical example of an identity is a username, and of course
usernames can include all sorts of interesting human-language
characters, so the application may want to accept unicode strings, and
convert them (deterministically) into bytestrings before passing them to
the library. There are, unfortunately, multiple ways to convert weird
unicode strings into UTF-8 (look up "surrogate pairs" sometime), but
there's one recommended canonical encoding ("NFC") that should work for
all but the strangest of inputs.

It's not entirely clear whether this conversion should be performed by
the application or the library. The problem with doing it in the
application is that using compatible SPAKE2 libraries may not be enough
to achieve interoperability (if the applications encode differently),
and everything will seem to work fine until a sufficiently novel
username is encountered. The problem with doing it in the library is
that it drags unicode into an otherwise somewhat clear-cut API, and
hampers the application from using full 8-bit bytestrings if it should
choose (perhaps the identities are public keys from some other system:
they'd have to be encoded as unicode before passing into such an API).

My recommendation is to have the library accept a bytestring, but
provide guidance on what the application should do with unicode
identities (which should be "encode with UTF-8 and NFC").

The two identities must be given to ``start()``, and must be included in
the state object so they can also be used inside ``finish()``. They
should be passed as arguments with "A" and "B" in the names, so that the
other library gets them the same way around, even if the actual argument
names are different (e.g. ``idA`` vs ``identity_A``).

If Carol and Dave are using this protocol, and Carol passes
``idA="Carol"`` and ``idB="Dave"``, then Dave must also pass
``identity_A="Carol"`` and ``identity_B="Dave"``. If Carol says
``side=A``, then Dave must say ``side=B``.

* What python-spake2 does: bytestrings
* What draft-irtf-crfg-spake2-03 does: bytestrings
* Symmetric mode: there is only one identity, named "idS", but it can
  still be set to an arbitrary string to distinguish between different
  applications

### The Group and Generator

The details are beyond the scope of this post, but SPAKE2 uses "Abelian
Groups", which contain a (huge) number of "elements". When our group is
an "elliptic curve" group, each element is also known as a "point" (the
elements of integer groups are integers, and other groups use other
kinds of elements). So you'll see references to "point encoding" and
"point validation". The other thing to know about groups is that there's
a second thing called a "Scalar", which is just an integer, limited to a
range between 0 and a big prime number (which depends on the group).
Sometimes you'll need to deal with group elements, sometimes you'll need
to work with scalars.

Some groups are faster than others, or have smaller elements and
scalars, or are more or less secure.

The Ed25519 signature protocol defines a group (sometimes named
"X25519") with nice properties, but you could use others. My python
library defaults to Ed25519 but also implements a couple of integer
groups.

Both sides must use the same group, of course. Every group comes with a
standard generator to use for the base-point "scalarmult" operation, and
the group's order will constrain many other choices.

* What python-spake2 does: defaults to Ed25519, but offers
  1024/2048/3072-bit integer groups too.
* What draft-irtf-crfg-spake2-03 does: left as an exercise for the
  reader, but sample M/N values are generated for SEC1 P256/P384/P521,
  and Ed25519 gets a passing mention

### Password

The input password should be a bytestring, of any length (your library
shouldn't impose arbitrary length limits). Any necessary encoding should
be done by the application before submitting a bytestring to the SPAKE2
library (if the application needs to allow humans to choose the
password, then it may want to accept unicode and perform UTF-8 encoding
itself).

The same arguments for identities apply here, but I'm even more in favor
of a bytestring API (rather than unicode), because it's entirely valid
to have the password be the output of some other hash function (maybe
you stretch it with [Argon2](https://www.argon2.com/) first), in which
case requiring a unicode string would be messy.

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

Nominally, this only ever needs to be done once. I could copy the M and
N values from python-spake2 into spake2.rs (as a big hex string) and
include a note that says "if you want proof that these were generated
safely, go run python-spake2". But it'd be nice to be more transparent,
which may require porting the specific seed-to-arbitrary-element
algorithm into the new language too.

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


### Element Representation and Parsing (Encode/Decode)

Element representation is the most obvious compatibility-impacting
decision to make, as the algorithm provides a group element (e.g. a
point) for the first message, but our library API returns a bytestring.
So clearly we need to define how we turn group elements into bytes, and
back again.

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
*safely* for other random strings, including deliberate modifications of
otherwise-valid values by an attacker. There is some debate about the
issue, but for safety, the receiving side should reject any message
which turns into:

* a point that's not actually on the right curve
* a point that's not actually a member of the expected subgroup

The former is accomplished by testing the recovered X and Y coordinates
against the curve equation, which takes time. The latter is done by
multiplying by the order of the group (the details of which depend upon
the "cofactor"), and can take as much time as the main SPAKE2 math
itself (so potentially doubling the total CPU cost). However both are
important to do, and worth the slowdown.

Note that whatever crypto library you use will probably implement
point-encoding and decoding for you. In general, this is great, because
they probably did a much better job of it than anything we could do. But
this also limits your ability to interoperate with a SPAKE2 function
that uses a different crypto library. And check the docs carefully to
make sure it's doing enough validation: you might be using a function
that assumes the encoded values come from a trusted source (e.g. saved
to disk), and that's not the case for us.

Finally, SPAKE2 is (usually) "sided": there are two roles to play, and
both participants must somehow choose (different) sides before they
start. A really common application mistake is to use the same side on
both ends: "Hello Alice? This is Alice.". When this happens, the keys
won't match, and the result will be indistinguishable from a password
mismatch, which will take forever to debug.

To help programmers discover this error earlier, the library might want
to add a "side identifier" to the message. If the second API function is
given a message from the same side as it was told to be in the first
function, it can throw an exception.

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/ed25519_basic.py#L342):
  encode points like Ed25519 does, reject not-on-curve and
  not-in-correct-subgroup points during parsing. A one-byte "side
  identifier" is prepended to the outgoing message, and this identifier
  is checked and stripped on the inbound function.
* What draft-irtf-crfg-spake2-03 does: specified by the choice of group,
  suggests SEC1 uncompressed or big-endian integers

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

```
def safe_hashcat(a, b):
    return sha256(a).digest() + sha256(b).digest()
```

* [What python-spake2 does](https://github.com/warner/python-spake2/blob/v0.7/src/spake2/spake2.py#L45):
  transcript =
  sha256(password)+sha256(idA)+sha256(idB)+msg_A+msg_B+shared_element.to_bytes()
* Symmetric Mode: sort the two messages lexicographically to get
  msg_first and msg_second, then transcript = sha256(password)+sha256(idS)+msg_first+msg_second+shared_element.to_bytes()
* What draft-irtf-crfg-spake2-03 does: len(A)+A+len(B)+B+len(B_msg)+B_msg+len(A_msg)+A_msg+len(shared_element)+shared_element+len(password_scalar)+password_scalar

In draft-irtf-crfg-spake2-03, `len(x)` uses 8-byte little-endian
encoding. The shared element is encoded the same way as it would be on
the wire. The hash uses the password scalar, rather than the password
itself. All fields are length-prefixed even though most of them have
fixed lengths.

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
* What draft-irtf-crfg-spake2-03 uses: left as an exercise

### Things That Don't Matter

SPAKE2 implementations must also choose a random secret scalar. They'll
use this to compute the message that gets sent to their peer, and then
they use it again on the message they receive from their peer. They need a fresh new scalar each time they run the protocol.

This scalar be chosen uniformly from the full range (excluding 0, so
from 1 to P-1 inclusive). The considerations and techniques described
above are all important, however since this is kept secret, it doesn't
actually matter how any given implementation does it.

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
