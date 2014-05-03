
Two building blocks to rely on in security systems: behavior of objects, and
(crypto) math.

Behavior doesn't involve crypto, but does involve being able to protect the
integrity (and usually confidentiality) of some bundle of state. There must
be an actor somewhere.

Crypto doesn't require an actor, but tends to be more limited in what it can
protect.

Things that require behavior:

* "don't decrypt this until Tuesday"
 - math has no concept of time. You could ask an actor to not reveal a
   decryption key until tuesday, but there is no way to achieve such behavior
   without relying on an actor.
* "is this signature valid?"
 - the actual verification is math, but the result is a boolean, which can't
   trigger or reveal anything

Things math can handle / work with:

* "is X known?", where X is a long secret and the function that uses it
  requires an exact match. You could use X as an AES key, and "do" something
  like reveal some Y by encrypting the Y. In practice, Y is only revealed to
  someone who learns X and acts on it, but to model it conservatively, it may
  be best to treat knowledge of X as a universal boolean: "X has been
  revealed (to the universe)" rather than "Bob knows X (but not Carol)".

Math can do threshold decryption: out of X1/X2/X3/X4/X5, three or more of
them must be revealed to decrypt Y. But there's no practical concept of "at
the same time", or "by the same person": that relies on an actor (who learns
X1) to forget it after that "same time".

math can sense:
* "is X known?"
* threshold decryption

math can do:
* reveal Y
