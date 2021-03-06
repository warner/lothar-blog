
In 2008, Zooko and I published a
[paper](http://eprint.iacr.org/2012/524.pdf) describing (among various
Tahoe-related things) "semi-private keys". Since then, I've learned that
the basic concept has been independently re-invented multiple times.
This post is an attempt to gather the various use cases which prompted
this, and compare how each one is using semi-private keys to accomplish
related goals.

## Semi-Private Keys in general

Standard signing/verifying systems produce two classes of keys, where
you can derive the "weaker" key from the "stronger" one, but not the
other way around:

* 1: private signing key
* 2: public verifying key

The idea of semi-private keys is to somehow extend this into a three-key
system.

* 1: signing key
* 2: middle key
* 3: verifying key

The first key lets you sign things, and the last key lets you verify
things, but there's also a middle key. You can derive "down" from the
middle key into the verifying key, but not "up" to recover the signing
key. And knowing the verifying key isn't enough to derive the middle
key.

These three keys can also be associated with symmetric keys (perhaps
just by hashing the key itself), which yields three classes of symmetric
encryption.

The core idea can be extended to produce semi-semi-private keys (four
classes) and beyond.

When we originally wrote this up, we also envisioned encryption-based
systems, not just signing. A semi-private encryption system would have
the decryption key be the most powerful, and a public-key encryption key
on the least-powerful end. So far we haven't come up with a use for
this, but in theory it should be possible to build.

## Tahoe-LAFS Mutable Files

Tahoe's mutable files are based on signed encrypted **shares** which are
published to storage servers, then retrieved by anyone who wants them.
Access control is implemented by distributing three "capability
strings": writecaps, readcaps, and verifycaps.

The writecap is generated when creating the mutable slot, and knowing it
grants the holder the authority to modify the slot (by signing new
versions of the share). Each time the writer wants to change the
contents of the mutable file, they encrypt the new plaintext, sign the
resulting ciphertext, and upload the result to the storage servers at an
index determined by the verifycap.



Users and compute nodes are partitioned according to which of these
strings they know, and all are unguessable (except as derived from each
other).

The publisher of the file creates a "writecap", which gives them the
ability to sign new shares (and encrypt the data which they write into

writecap -> readcap -> verifycap

maybe writecap -> readcap -> deep-verifycap -> (shallow-)verifycap

The scheme we came up with looked like this:

* writecap = `x` (a random scalar)
* (signing key = `H(x*B)*x` (scalar))
* readcap = `x*B` (element)
* verifycap = verifying key = `H(x*B)*x*B` (element)

The one-wayness is clear for everything except the verifycap->readcap
step. The usual approach to proving this is safe is to assume that it's
not (i.e. assume you have a machine takes a verifycap and returns the
readcap), then use that machine to break one of your components (e.g.
use it to compute a discrete log, or a hash preimage). For our scheme,
this machine inverts the decidedly funky `f(Y)=H(Y)*Y` function. The
machine breaks two generally-considered-strong primitives **at the same
time**, intermingled with each other, and it's not clear that you can
use this to break either of the individual primitives in isolation.

## Tor

Onion Service publisher -> client -> DHT storage node

* publishing key = `x` (random scalar)
* onion address = `Y=x*B` (element)
* daily publishing key = `x+H(day+Y)`
* daily verifying key = DHT index = `Y+H(day+Y)*B`
* daily encryption key = `H2(day+Y)`

In the partially-implemented (and not-yet-deployed)
["next-generation hidden services"](https://gitweb.torproject.org/torspec.git/tree/proposals/224-rend-spec-ng.txt), the
.onion address is just an encoded form of the long-term base public
verifying key (which is never actually used to verify anything). Each
day, the service host computes a new daily keypair, by adding a
deterministically-generated random number to their base private
(signing) key. Clients (who know the onion address) can do the same
computation on the base public key, to produce the daily public key.

Both the hosts and the clients also compute a daily symmetric key, by
hashing the day number with the onion address. The host encrypts their
descriptor record with this daily symmetric key, signs it with the daily
private key, then uses the daily public key as a Tahoe-style "storage
index". This storage index determines which DHT nodes will hold the
record, and is also used as a slot index on those nodes to indicate
which record is being stored or retrieved. The storage nodes refuse to
accept unsigned data, and the storage index provides the verifying key,
so each slot can only be filled by the right publisher.

One final trick: the daily keys use a hash that also includes a
"randomness beacon": a string that is unknown to anybody until about 48
hours before it gets used, constructed by the nine primary directory
servers collaboratively hashing random strings together. With
commitments and voting, the process is designed to make it hard for any
subset of those servers to control the results. They want this
randomness to prevent attackers from camping out on the DHT nodes in
exactly the places where a given onion service descriptor is going to be
served in the future. An attacker who could do this for a long time
would be able to gauge the popularity of an onion service by counting
the requests for that descriptor. It might also be able to mount an
attack by corrupting the responses and watching for clients to
re-request the descriptor from other nodes.

There is a proof of soundness for this scheme:
https://www-users.cs.umn.edu/~hopper/basic-proof.pdf

## Bitcoin

Base private key -> POS terminal -> sender

BIP32

## Dual EC
## Ed25519 key ratchet?

# Actually Implementing Semi-Private Keys

Our paper only sketched out the abstract idea for DSA-ish signatures.
Tony Arcieri drew up a plan for implementing semi-private keys using the
Ed25519 signature algorithm, which requires some changes to the way
Ed25519 derives the internal nonce-generating values. He's got some
great diagrams and SAGE code at https://gist.github.com/tarcieri/4760215
.

To derive the keys, this implementation requires access Ed25519 clamping
function (which must be used twice), the internal scalar multiply
function (used twice for key generation, rather than once), and a
scalar*scalar multiplication (modulo the group order, which is normally
only used while making signatures). All these pieces are available to
the internals of an Ed25519 library, however they aren't usually exposed
to callers. So implementing this will require some modifications to
existing code.
