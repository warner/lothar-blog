Slug: 51-protocol-not-taken
Date: 2014-03-26 17:16
Title: The (protocol) Road Not Taken

Firefox 29 shipped in late april with a new password-based Sync
setup process. The protocol, named "onepw", is
[defined here](https://github.com/mozilla/fxa-auth-server/wiki/onepw-protocol).
This [replaces](../49-pairing-problems) the J-PAKE pairing-based protocol that we'd been using since
Firefox 4.0 in March of 2011.

But until last December, we were planning to use a larger protocol, now known
as "that old SRP-based KeyServerProtocol", which is
[specified here](https://wiki.mozilla.org/Identity/AttachedServices/KeyServerProtocol).

## The Good

The old SRP protocol had the following nice security properties:

* Doesn't rely on TLS (mostly).
* Strong defense against a fully-compromised server

With the exception of the initial account-creation message (and the
I-forgot-my-password reset message), the whole protocol would be secure even
if SSL were broken and attackers were reading all the API requests. A
TLS-level eavesdropper would get zero information about your password or
encryption keys, making them no more powerful than a regular online
password-submitting attacker. This would let us sleep better at night, in the
face of compromised CAs and all the recent flaws found in TLS/SSL.

Login servers need to store "password verifiers": data that can be used to
determine whether you (the purported user) really know the correct password.
These verifiers are created by running a CPU-intensive "key-stretching"
operation on the password, to make it harder to peform an "offline guessing
attack" against the password. This is a secondary line of defense against an
attacker who gets a copy of the verifier (e.g. using a SQL injection attack,
or stealing an old backup tape).

However, in most systems the user starts by sending their raw password over
the wire, and it's the server which performs the key-stretching. As a result,
the raw password is visible to any attacker who gets full control over the
server (arbitrary code execution), or can read the wire traffic after the SSL
protection has been removed (e.g. inside a datacenter, after an
SSL-terminating frontend box).

In our protocol from last December, the raw password was never sent to the
server: instead, we used a cryptographic protocol named
[SRP](http://srp.stanford.edu/). All key-stretching was performed on the
client, before talking to the server, so the attack-resistance of the
password was uniformly high.

## The Bad

However, our protocol had the following drawbacks:

* SRP is underspecified and not widely used
* Clients must run a CPU-intensive password-stretching operation for each login
* The server cannot perform additional stretching, to improve security.

SRP is relatively old (first published in 1998, same as AES), but is still
not a very common cryptographic tool, which always makes system designers
nervous. We had to write our own Node.js -compatible
[implementation](https://github.com/mozilla/node-srp) of SRP, which means new
bugs. "New" is always scary, and we encountered pushback for both the
relative complexity of the protocol, and the immaturity of our codebase.



But the biggest worry was the client-side key-stretching. Traditional login
systems use very small clients (just enough code to deliver the password),
and do all of the heavy-lifting on the server, where you have consistent CPU
power: you know that X million users will require Y computers to handle the
load.

Our use of SRP meant that any key-stretching **must** take place on the
client, before the SRP calculation begins. And clients are a varied
environment: ranging from high-end modern desktops to old slow
memory-constrained not-so-"smart"-phones. We couldn't predict how long any
given amount of key-stretching would take, making it hard to decide on an
appropriate amount. We could have made it adaptive (limit the stretching to
one second, do as much you can within that constraint), but then the variety
of devices within a single account is a problem: if you create the account
with a fast desktop, then access it with a slow phone, the phone's
key-stretching will take forever. And if we lowball the settings to enable
slow phones to have a good experience, then we're compromising security for
accounts that only use faster devices.


## The Ugly (Decision)

So we decided to shelve the SRP-based protocol and use the simpler
["onepw"](https://github.com/mozilla/fxa-auth-server/wiki/onepw-protocol).
instead. As cool as SRP was, we were nervous about painting ourselves into a
corner by having the client do so much of the work. By doing the bulk of the
stretching on the server, we can improve the protection in the future (by
doing more stretching, or using techniques from the upcoming
[Password Hashing Competition](https://password-hashing.net/)). And we can
provide a more consistent experience to users of all kinds of devices.
