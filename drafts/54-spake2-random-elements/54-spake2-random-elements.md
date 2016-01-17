Slug: 54-spake2-random-elements
Date: 2016-01-16 15:58
Title: SPAKE2 "random" elements
Category: security

!BEGIN-SUMMARY!
SPAKE2 requires two special "arbitrary" constants M and N. What properties do these constants really need? What attacks are possible if these requirements are not met?
!END-SUMMARY!

[SPAKE2](http://www.di.ens.fr/~pointche/Documents/Papers/2005_rsa.pdf), like all PAKE ("Password-Authenticated Key Exchange") protocols, allows two people start with a weak password and then agree upon a strong shared key, despite active attackers getting in the way. There are a variety of protocols in this family: SRP is probably the most well-known (but has the weakest security proofs), and J-PAKE is the one we used in the original Firefox Sync. But SPAKE2 is my current favorite: it's simpler, faster, and has a better security reduction.

## How SPAKE2 works

Assume the following notation: we have some group with generator B, we use additive notation (so `B*x` instead of `g^x`), lower-case letters are scalars, upper-case letters are elements, and `*` represents scalar multiplication.

Now the basic exchange looks like this:

one-time setup:

* choose `M` and `N` as random group elements

the protocol:

* Alice knows `pw1`, Bob knows `pw2`, hopefully the same
* Alice chooses random secret scalar `x`, sends `X = B*x + M*pw1`
* Bob chooses random secret scalar `y`, sends `Y = B*y + N*pw2`
* Alice computes `Z1 = (Y-N*pw1)*x`, then `K1 = hash(X,Y,Z1,pw1)`
* Bob computes `Z2 = (X-M*pw2)*y`, then `K2 = hash(X,Y,Z2,pw2)`

The promise of PAKE is that `K1` and `K2` will be the same **if and only if** the `pw1`/`pw2` passwords were the same. If they were different, then the keys are completely unrelated. For SPAKE2, this property stems from `Z1` and `Z2`.

This means a passive attacker has no hope of figuring out the shared key: from their point of view, all keys are equally likely, as are all passwords.

An active attacker only gets one guess (or maybe two, depending upon how you count). They make this guess by pretending to be Bob and running the protocol as normal. If their `pw2` guess was right, they'll get the same key as Alice, and they win: they know the password *and* the key. Then they turn around and pretend to be Alice, using the successfully-guessed password in a protocol run with Bob, which should succeed (with a different key). Now that they know both session keys, they can MitM the Alice-Bob connection like they would with traditional unauthenticated Diffie-Hellman.

If their guess was wrong, the session keys are independent and unrelated, and they won't be able to talk with Alice (or Bob) at all. For each time that Alice or Bob is willing to run the protocol, they get another guess.

(incidentally, both sides usually include some sort of identity string in their transcript hashes, so an attacker can't splice together unrelated sessions: Alice runs this protocol with a specific intent to construct a session key for server "foo.com", and can't be confused by a response that was replayed from an earlier session with "bar.com")

## Where do M and N come from?

The original paper describes M simply as "an element in G associated with user A". A different paper (Boneh) describes M and N as "randomly chosen elements of G". While it's probably obvious to an experienced student of cryptography (which I am not), it turns out that what really matters is that **nobody knows the discrete log** of M and N. That is to say, nobody knows a scalar `m` for which `M = B*m`, and likewise for N.

If you don't realize this, and you're struggling to figure out how groups work anyway, you'd probably make the same mistake that I did, and construct M by choosing an arbitrary scalar (just a large number, modulo the group order `|G|`), and scalar-multiply it by the base point. My first implementation used `11*B` and `12*B`, which seemed sufficiently arbitrary to me :-). When I showed it to Mike Hamburg, he kindly pointed out the necessary properties of M and N, and I eventually figured things out. You can't start with a scalar and multiply your way to an element: you must somehow start with an element.

The traditional way to prove that nobody knows the scalar is to hash some simple string (with limited wiggle room) and somehow convert the hashed output into an element. Popular strings include pi, e, sin/cos functions, and the names of the parameters themselves. The nominal argument is that you'd have to tamper with the fundamental constants of the universe to have enough control over the output to steer it towards an element for which you already knew the discrete log.

It turns out to be much easier to choose an arbitrary element in an integer group, like `Zp*`: you treat the hash output as a random member of 0..p-1, then just raise it to `q` (the order of the subgroup). The result will be in the right group and will be just as uniformly distributed as the hash output itself. There's an example [here](https://github.com/warner/python-spake2/blob/v0.3/spake2/groups.py#L132).

For elliptic curves, you must turn the hash output into an x (or y) coordinate, recover the other coordinate (giving you a point on the right curve, but not necessarily in the right group), then either check the group order or just multiply (known as "clearing the cofactor"). [Here](https://github.com/warner/python-spake2/blob/v0.3/spake2/ed25519_basic.py#L269) is the function which does this in my [python-spake2](https://github.com/warner/python-spake2) implementation.

## Why must M be random?

A thing that puzzled me up until now was why, exactly, it was so important that nobody knows the discrete logs for these constants. I knew there was some sort of attack possible, but I couldn't figure out the details. Mike Hamburg pointed me in the right direction in [his discussion](https://moderncrypto.org/mail-archive/curves/2015/000424.html) of "SPAKE2 - Elligator Edition" on the moderncrypto.org [curves mailing list](https://moderncrypto.org/mailman/listinfo/curves). But I didn't work out the attack until just recently.

Here's the deal: an active attacker (pretending to be Bob) who gets some sort of offline oracle access to the final session key will be able to mount an offline dictionary attack against the password that Alice used. "Oracle access" means they get to observe some use of that key: maybe Alice immediately sends a key-confirmation message (a simple hash of the key) so Bob can tell whether the PAKE succeeded or not (the oracle is then just hashing the potential key and seeing if it matches the confirmation message). Or Alice uses the key for authenticated encryption, and sends a ciphertext where the attacker can see it (so trial decryption of that message provides the oracle). Because the oracle is **offline**, the attacker can test guesses of `K1` as frequently as they like, without additional interaction with Alice.

Suppose that the attacker knows that `N = B*n` (`n` being the discrete log of the no-longer-arbitrary point `N`).

Now, when our attacker Mallory pretends to be Bob, she picks a random `y` and sends `Y = B*y`, omitting the password and blinding factor `N` entirely. Mallory receives `X = B*x + M*pw1` from Alice. Note that `B*x = X - M*pw1`.

Alice will then compute `Z1 = (Y-N*pw1)*x`, which is really `(Y-B*n*pw1)*x`, which is really `(B*y-B*n*pw1)*x`, which (since scalar multiplication is associative) is really `(y-n*pw1)*B*x`, which means `Z1=(y-n*pw1)*(X-M*pw1)`.

Note that every term in that final equation is known to Mallory except the password `pw1`: she picked `y` herself, `n` is the discrete log of `N`, and `X` was given to her by Alice. Mallory has all the time in the world to try various values of `pw1`, compute a potential `Z1`, and test the resulting session key `K1` against the oracle.

This only works if Mallory can factor out the `B*something` in Alice's `Z1` computation, which is why she needs the discrete log of `N` to pull it off.

Of course, if `N` were chosen safely, but `M`'s discrete log were known, then Mallory would pretend to be Alice instead of Bob. Hamburg pointed out that if you can constrain the order of the messages, and have Alice prove herself to Bob first, then it's safe to drop **one** of the blinding factors entirely (send `B*x` instead of `B*x + N*pw`). But if the protocol isn't constrained this way, you must have both.

## Weaker things

M and N might not be completely independent, but still nobody knows the discrete log of them. For example, maybe:

* we know that N is some constant times M (hence `n` is some constant `k` **plus** `m`)
* we know that N == M (e.g. `k=0`)

I don't think these result in attacks, but I'm still looking for papers to prove it. I'm told that the [2003 Kobara/Imai paper](http://eprint.iacr.org/2003/038.pdf) proves this, and Mike told me that M==N yields a proof that reduces to the CDH-Squared problem instead of the usual CDH (Computational Diffie-Hellman) problem, but that they're basically the same thing.

I especially want M==N to work because that makes the message flows in [magic-wormhole](https://github.com/warner/magic-wormhole) easier. If M and N are distinct, then the two sides need to agree (ahead of time) which role they're going to play. If M==N then the protocol is much more symmetric, and the humans constructing offline wormhole codes don't need to choose sides as well.

I use the M==N form in python-spake2's [SPAKE2_Symmetric](https://github.com/warner/python-spake2/blob/v0.3/spake2/spake2.py#L209) class, and in [magic-wormhole](https://github.com/warner/magic-wormhole/blob/0.6.2/src/wormhole/blocking/transcribe.py#L284) itself.
