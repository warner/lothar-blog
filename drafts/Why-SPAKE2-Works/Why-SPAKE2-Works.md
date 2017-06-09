Slug: Why-SPAKE2-Works
Date: 2017-05-31 13:52
Title: Why SPAKE2 Works
Category: cryptography

!BEGIN-SUMMARY!
SPAKE2 is a PAKE (Password-Authenticated Key Exchange) algorithm, which
allows two parties who know the same low-entropy secret to safely derive
a high-entropy shared key. How is that possible?
!END-SUMMARY!

## Diffie-Hellman

Before you can be convinced that SPAKE2 works, you need to be convinced
that the
plain [Diffie-Hellman](https://en.wikipedia.org/wiki/Diffie_hellman) key
agreement algorithm works. DH is an **unauthenticated** key-agreement
algorithm: when you run it, you will wind up with a strong key with
**somebody**, but you don't know with whom.

You could be the victim of a classic "man-in-the-middle" attack, where
you (we'll pretend your name is Alice) wind up sharing a key with the
attacker (usually named Mallory), and Mallory shares a different key
with your intended partner ("Bob"). Mallory can just decrypt your
message with her copy of the Alice-Mallory key, then re-encrypt them
with the Mallory-Bob key, and neither of you would be the wiser.

To overcome this, unauthenticated key-agreement protocols must be
supplemented with some step that binds the key to the intended
identities: e.g. Alice signs a hash of (her session key, her name, Bob's
name), and sends it to Bob. If Mallory is in the middle, then Alice will
sign ``Alice-Mallory key, "Alice", "Bob"``, and that won't match what
Bob sees. Mallory can't forge Alice's signature, so she can't replace
the message with one that *would* meet Bob's expectation.

Adding authentication to plain DH requires that Alice and Bob already
know each others' public keys. And that they even have public keys to
begin with. There is a whole family of Authenticated Key Exchange
algorithms, unsurprisingly named "AKE", to get a strong session key from
strong long-term keys (public or secret).

It wasn't always the case, but these days we describe DH as a
"key-agreement" protocol, rather than "key-exchange". "Agreement"
usually means that the session key combines contributions from both
parties, so it just pops out of the protocol at the very end. In
contrast, an "exchange" protocol typically has one party decide on the
session key, then somehow encrypts it so that it can only be read by the
intended recipient. Many of the algorithms with "AKE" in the name are
really key-agreement, but "AKA" isn't as easy to pronounce.

## PAKE

*Password*-Authenticated Key Exchange uses a shared *short* secret to
authenticate the other party, instead of a pair of public keys. Both
sides (Alice and Bob) feed their password into a machine, and the two
machines exchange messages. At the end of the process, each machine
emits a key. If the passwords were the same, the keys will be the same,
and the shared key will be random and statistically independently from
any of the observeable message exchanges. If the passwords were
different, then the keys will be different.

The security of the scheme is obviously limited by the length (or more
precisely, the *entropy*) of the password. It's also limited by the
number of times you re-use the same password. In a secure PAKE protocol,
the attacker's best chance is to simply pretend to be Bob and make a
guess at the password, giving them exactly one guess.

## Scalars and Groups

All these protocols are based on a **group**. This is a math concept
where you've got a bunch of "group elements" and a specific binary
operation (which we call "+", but it might not look like grade-school
arithemetic at all). The rule is that "adding" any two group elements
always gives you another group element: it's not possible to escape the
group by adding.

One such group is the integers from 0 to 6, and we define "+" to be
"add, then reduce modulo 7". Any prime number will do: 0..12 and "add
modulo 13" is also a group.

Groups aren't limited to integers. Another common group uses polynomials
with coefficients that are either 0 or 1. The most useful groups for
modern crypto, however, use points on an elliptic curve as elements.
These points can be represented as integer X and Y coordinates in some
range (like 0..``2^255-19``) which meet the curve equation (something
like ``y^2 - x^2 - d*x^2*y^2 = 0``, all modulo some large prime).
"Addition" is a bit funky, but it can be defined in such a way that you
always stay within the group.

For crypto, we specifically use a finite cyclic abelian group in which
the discrete-log problem is assumed to be hard. One consequence of these
constraints is that the size of the group will be a large prime number,
which we'll call ``P``. Also, there's a "zero" element (and adding
"zero" to anything else leaves it alone, like you'd expect).

"Addition" always takes two group elements and produces a third. You can
repeat the addition process multiple times, which we call "scalar
multiplication". For example we define ``scalarmult(4,M)`` as
``add(add(add(M, M), M), M)``. We don't use repeated addition in
practice: there are much more efficient ways to do it (linear in the
size of the group, but constant in the magnitude of the scalar). Scalar
multiplication always takes a scalar and an element. In the papers that
I've seen, scalars are usually held in variables with lower-case names,
and elements get upper-case names. Scalar multiplication is expressed by
concatenating a scalar with an element, so ``xM`` means ``scalarmult(x,
M)``. There also seems to be a preference to keep the scalars on the
left and the elements on the right, so they'd use ``xM`` rather than
``Mx``. I kind of prefer to use ``*`` for scalar multiplication.

**Scalars** are just integers between 0 and the size of the group. A
second consequence of our group constraints (the "Abelian" one) is that
scalars are equivalent modulo P, and you can always reduce the scalars
in an equation by P. So ``scalarmult(x, scalarmult(y, M))`` is exactly
equal to ``scalarmult((x*y)%P, M)``, which is pretty handy for
performance, since multiplying scalars together is usually much faster
than performing a scalar multiplication.

Another consequence is that there will be at least one "generator". This
is some group element ``G`` which, when scalar-multiplied by all scalars
from 0 to P (i.e. ``0*G``, ``1*G``, ``2*G``, .. `(P-1)*G`), gives you
all group elements. This one-to-one mapping of scalars to elements is
pretty important. Most groups come with a standard generator "base
point", e.g. the Ed25519 elliptic-curve group defines its generator as
the point with Y coordinate 4/5 (since the curve is symmetric around the
Y axis, there are only two such points, and they choose the one where
the X coordinate is "positive". The distinction between positive and
negative is weird when the coordinates are really integers modulo a
256-bit prime, but it's well-defined and not too difficult to work
with). Groups typically have lots of generators (in fact another
consequence of being Abelian is that *every* element is a generator),
but we always agree on just one as a base point.

I like to think of the elements as rocks of different shapes, to avoid
the trap of treating them like well-ordered integers. I draw a circle,
and put the scalars (from 0 to P-1) around the inner ring. Then I place
the elements around them, one ring out. 0 maps to the zero element, 1
maps to the generator ``G``, 2 maps to ``scalarmult(2, G)`` (aka
``G+G``), 3 maps to ``3*G``, etc.

We specifically picked a group in which the "discrete log problem" is
hard, but basic operations (addition and scalar multiplication) are
easy. That means it's relatively quick to scalarmult from scalar out to
element, but "hard" (as in "not enough computrons in the universe" hard)
to go the other way. You can pretend that each rock (element) has a
scalar hidden inside it, where it remembers its place on this first ring
(i.e. the discrete log to base ``G``), but given just the element, it's
impossible to dig this secret scalar out.

Yet another useful property of these groups is that scalarmult by *any*
scalar (other than 0) is a **permutation** from elements to elements.
Scalarmult by 1 is a no-op, so that's not so interesting, but using any
other scalar gets you a random mapping. And this mapping is one-way:
given two elements X and Y, and being told that ``Y = nX`` for some
``n``, it's "hard" to figure out what ``n`` could be (this is the
discrete-log problem again, except to base ``X`` instead of base ``G``).

To visualize this, I imagine adding a second ring of rocks around the
first, perhaps labelled "Multiply by 3". Each element (rock) in the
outer ring is obtained by doing ``scalarmut(3, X)`` with the element in
the inner ring. This is a permutation: every kind of rock will appear
exactly once in each ring. If we could peek inside the rocks and see
their secret scalars, we'd notice that the scalars in the outer ring
were always equal to 3 times the scalars in the rocks in the inner ring
(well, ``3*x%P``). But since we can't break open the rocks to see those
scalars, all we see is a permutation.

We can define "subtraction" to work like we're used to. Since scalars
are all modulo P, we can define ``-X`` as being ``scalarmult(P-1, X)``,
and then ``X-X=0`` as we'd expect. We can do this because we know the
size of the group (P): if we didn't, then subtraction would be
expensive.

Probability theory tells us that if we start with a random variable,
then transform it with a permutation, we wind up with an equally random
variable. Starting  ...



The final important component is that scalarmult is commutative, so
``x*(y*G) == y*(x*G)``. (It also equals ``(x*y)*G``, where we only do a
single scalarmult, but that's not very useful). Making two rings
(scalarmult by x, then scalarmult by y) gets you rocks in exactly the
same order as making the rings using y and then x. The middle ring is
completely different, but the outer ring will be the same.


## How DH Works

Ok, now that we know the background, how does plain (unauthenticated)
Diffie-Hellman work? Basically, each side chooses a random scalar (Alice
picks ``x``, Bob chooses ``y``, each uniformly random from the range
0..P), then multiplies by the generator (Alice gets ``X=xG``, Bob gets
``Y=yG``), then sends this element to the other side while keeping the
scalar to themselves. Upon receipt, each side multiples the received
element by their secret scalar to get their new (hopefully shared)
element. Alice computes ``K=xY`` aka ``scalarmult(x,Y)``, and Bob
computes ``K=yX``.

* Since the operations are commutative, they'll both get the same
  element.
* The shared element is uniformly distributed among all group elements.
  This follows from having either ``x`` or ``y`` being uniformly random.
  If ``x`` weren't random, multiply by random ``y`` would get you a
  uniform distribution. Likewise any non-uniformities in ``y`` could be
  fixed by multiplying by a random ``x``. Since both sides pick their
  scalars randomly, the final shared element is random.
* The new shared element can be expressed as bits and then hashed into a
  shared encryption key. It's important to hash the value, because group
  elements have a lot of predictable structure to them, like maybe
  high-order bit is usually 1. Hashing removes this structure.
* In fact, it's good practice to hash an entire transcript of the
  conversation, to prevent an attacker from selectively mixing and
  matching pieces of different conversations. It doesn't matter much
  now, but in SPAKE2 it will become pretty important.
* The group elements exposed on the wire (``X`` and ``Y``) can't be
  reversed into the secret scalars, because we picked a group where this
  direction is hard. To be specific, we pick a group where the
  "Computational Diffie-Hellman Problem" is hard. The CDH problem says
  given ``(G, xG, yG)``, you can't compute ``xyG``. There are other
  flavors of this problem, like "Decision DH", but a lot of people treat
  them as roughly equivalent.

## How SPAKE2 works

In SPAKE2, Alice and Bob agree upon a couple of extra things:

* a way to turn passwords into scalars. Since scalars are just integers
  in a particular range, it's sufficient to just hash the password into
  a bunch of bits, treat the bits as a number, and then modulo down to
  the right range. The range needs to be large enough to map each
  password to a unique scalar, but I don't think it needs to be
  particularly uniform. We'll call this scalar ``pw``.
* they agree on a pair of group elements named ``M`` and ``N``. We must
  make sure that nobody knows the discrete logs of these elements. We'll
  use these to generate blinding factors.

Then we change the regular DH protocol a bit:

* Alice computes ``X = xG + pwM``. I.e. she builds a blinding factor by
  scalar-multiplying her password scalar by the pre-agreed element M,
  then she adds this blinding factor to the normal DH element.
* Bob does the same, but with ``N``, so ``Y = yG + pwN``
* They exchange ``X`` and ``Y`` as before
* Alice removes the blinding factor from Bob's message before she
  multiplies by her secret scalar. ``K=x(Y-pwN)``. Given how we defined
  "subtraction" before, we really do ``K = x(Y+(P-1)*pw*N)``. We can
  save a little time by pre-computing (P-1)*N, and we can perform the
  multiplication by pw while we're waiting for the other side's message
  to arrive.
* Bob does the same: ``K=y(X-pwM)``
* Both sides then hash a transcript of everything: X, Y, pw, and most
  importantly K. The result is the shared key.

After removing the blinding factor, this looks just like regular DH,
which is why both sides will get the same key if they used the same
password.

Now, the expectation of PAKE is that if the passwords are *different*,
then both sides will get random and unrelated values of K. Why is this
the case?

Alice's intermediate value of ``yG`` is a uniformly-random group element
(since ``y`` was a uniformly-random scalar). And her intermediate
``pwM`` is a group element that could be one of a small number of
possible values, depending only on the password.

To make things simple, let's pretend that there are only two possible
passwords, so ``pw`` is either 0 or 1. The PAKE expectations are met if
the attacker has just a 50% chance of guessing it correctly.

The ``Y`` value that the attacker sees is either ``yG``, or ``yG+M``.
Since ``yG`` is uniformly random, ``yG+M`` will also be uniformly
random, and the attacker can't tell the difference.

If Mallory pretends to be Bob and runs the same protocol, she has a 50%
chance of guessing incorrectly. Let's say that Alice used ``pw=0`` and
Mallory used ``pw=1``. Alice sends ``X=xG+0*M``, and Mallory sends
``Y=yG+1*N``. Mallory will compute ``K=y(X-1*M)``, which will be
``y(xG-M)``, which is ``yxG-yM``. Meanwhile Alice has computed
``K=x(Y-0*N)`` which is ``x(yG+N)`` which is ``xyG+xN``. The two keys
have the same shared ``xyG`` term, but differ by ``xN-yM``. Since Alice
picked her ``x`` to be uniformly random, and Mallory has no way to learn
``x``, ``xN-yM`` is uniformly random no matter how Mallory picked ``y``.
So Mallory's key will be statistically unrelated to the one that Alice
uses.

## Setting M==N

In many PAKE applications, one party is obviously a client, and the
other is clearly a server, and they can use these roles to decide who
uses M and who uses N. But in some, like Magic-Wormhole, it would
require additional negotiation to choose sides ahead of time. So I use a
variant of SPAKE2 in which we set M==N. The blinding still works in this
case, however the security proof then reduces to a slightly weaker
flavor of the Diffie-Hellman problem (CDH-Squared).






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
