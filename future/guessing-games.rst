How To Guess A Password
=======================


Why do we (i.e. web servers) hash user passwords before storing them? And how
does it help to add a salt to that hash? What's the big deal with ZKPs
(Zero-Knowledge Proofs) like SRP?

It's all about damage control, and about reducing authority. The web server
should have as little power as possible, so that anyone who manages to
compromise the web server (and steal its private data) can do as little
damage as possible.

What does the web server *really* need to be able to do? When you get right
down to it, the server just needs to know whether to accept any given
request. The current standard practice goes something like:

1: define "knowledge of password" as sufficient criteria for accepting
   requests
2: use a "login" process to test knowledge of the password and generate an
   access token
3: deliver the access token with each request, usually as a cookie

Now, there are all sorts of problems with this convention, many of which are
reactions to other limitations:

* password guessing: restricting the secret to something that a human can
  remember, while enabling unaided humans access their account on foreign
  computers, also limits the overall security, sometimes beyond repair
* phishing: the login process rarely gives users enough information about who
  is on the other end to safely prove knowledge of the password
* CSRF: cookies are "ambient", delivered with all requests whether initiated
  by the original server or not

I'm going to gloss over most of these so I can focus on how the login process
gets from knowledge of a password to a decision to accept a request, and more
specifically how this decision (and the stored data which supports it) can be
used to reverse-engineer the user's password (or something equivalent). For
the sake of argument, I'm going to mostly ignore phishing (i.e. pretend users
magically know when they're talking to the right site and never reveal their
password elsewhere), and declare the process finished when the server decides
to accept the login and emits the session cookie. I'm also going to pretend
that Alice and Bob have a secure way to set up their credentials ahead of
time.

We have our usual cast of characters. Alice (the client) claims to know the
secret, Bob (the server) is testing her knowledge. Eve (the eavesdropper)
gets to see them talk. And Ida (the intruder) has stolen a copy of Bob's hard
drive and gets to see anything he's stored away (we'll pretend that Bob can
securely delete things, so Ida can't observe the setup phase).

Sending Plaintext Passwords
===========================

The simplest imaginable way to prove knowledge of a secret would be familiar
to any six year old: you tell it to the server and they compare it to their
stored copy. And it has all the security you'd expect from something designed
by a six year old: anyone listening to the conversation now instantly knows
the secret, with no significant work. If you accidentally exercise your proof
in front of the wrong person, now they know it too. Oops.

Worst Case: Storing Plaintext Passwords
---------------------------------------

On the server side, Bob has several options, but the simplest thing he can do
is to store the passwords verbatim, which means that Ida knows the passwords
too. This is exactly what HTTP Basic Auth does, as well most frameworks that
allow "password recovery" (where the server will email you a password when
asked nicely).

Code:
 Setup: Bob stores verifiers[ALICE] = PASSWORD
 Alice: send PASSWORD to Bob
 Bob: grant access if PASSWORD == verifiers[ALICE]
Work Needed To Recover Password:
 Bob: 0
 Eve: 0
 Ida: 0

Hashed Passwords
----------------

The next most clever thing Bob can do is to hash the passwords before storing
them. The simplest approach is for Bob to record SHA256(PASSWORD) instead of
the raw PASSWORD. Now Ida can't get the password directly. But she can run
through a dictionary of likely passwords, hash each one, and compare it, and
if she gets a match, now she knows the password too. Because every password
is hashed the same way, she can do this in parallel for every entry in the
table. Worst of all, she can do this ahead of time, once, and spend hardly
any time at all doing the lookup (for certain situations, there is an
efficient time/space tradeoff called a "Rainbow Table" that fits onto a
DVD-ROM and can deduce the password in a few seconds).

The work it takes to guess a password is the number of passwords that need to
be guessed (on average, you'll have to search half the dictionary before you
find the word), multiplied by the time it takes to check each guess. Thanks
to Bitcoin, modern parallelized GPUs can perform a nearly a billion SHA256
hashes per second, so we'll define Tsearch as 1ns.

Code:
 Setup: Bob stores verifiers[ALICE] = sha256(PASSWORD)
 Alice: send PASSWORD to Bob
 Bob: grant access if sha256(PASSWORD) == verifiers[ALICE]
Work Needed To Recover Password:
 Bob: 0
 Eve: 0
 Ida: Tsearch(=1ns) * len(dictionary) / num_users
      or less with precomputation

Salted Hashed Passwords
-----------------------

To prevent parallel attacks, Bob can hash each password slightly differently,
by using a "salt". Anyone who knows the stored hash can still do a dictionary
attack, but they have to do a *different* search for each one.

Code:
 Setup: Bob picks 256-bit random SALT, stores in salts[ALICE]
        Bob stores verifiers[ALICE]=HMAC_sha256(SALT, PASSWORD)
 Alice: send PASSWORD to Bob
 Bob: look up SALT=salts[ALICE]
      grant access if HMAC_sha256(SALT, PASSWORD) == verifiers[ALICE]
Work Needed To Recover Password:
 Bob: 0
 Eve: 0
 Ida: Tsearch * len(dictionary)
      or less with precomputation

Sending Hashed Passwords
========================

In all of this, Bob knows the password (at least during the setup phase, and
in some cases stored in the database). If Alice, like many people, uses the
same password on multiple sites, then Bob can probably get in to her accounts
on other sites too. A good network citizen will seek to do better. We'd
prefer that everyone use a system that doesn't let Bob know the password
either, even momentarily.

The first thing you might try is to have Alice send a hash of her password
instead of the original. Alice now has to do a little bit more work to
complete the protocol: she has to do one SHA256 hash of her password first.
She's only logging in once, so the massively parallel GPU farm in her
basement (maybe Alice and Ida are roommates) won't help her too much. In many
web scenarios, sites decline to use the built-in HTTP Digest Authentication,
so the hash algorithm must run in inefficient Javascript. Fortunately, SHA256
is still pretty fast, and a modern browser can probably finish it in
Thash=22us.

Code:
 Setup: Alice sends HASH=sha256(PASSWORD)
        Bob stores verifiers[ALICE]=HASH
 Alice: send HASH=sha256(PASSWORD)
 Bob: grant access if HASH == verifiers[ALICE]
Work Needed To Recover Password:
 Wp(Bob): Tsearch * len(dictionary) / num_users
 Wp(Eve): Tsearch * len(dictionary) / num_users
 Wp(Ida): Tsearch * len(dictionary) / num_users
Work Needed To Forge Login:
 Wf(Bob): 0
 Wf(Eve): 0
 Wf(Ida): 0
Work Needed To Complete Protocol:
 Wc(Alice): Thash(=22us)

When Alice sends something other than her password, we now have two figures
of merit. The first is how hard it is to recover the original password: this
is about protecting Alice's other accounts from one of our characters. The
second is how hard it is to recover something that allows a login with Bob:
this is specifically about protecting her account at Bob's. Clearly we don't
care about Wf(Bob), since Bob has control over her account anyways. But
Wp(Bob) is how Bob shows his concern about the rest of the internet, his
deliberate ignorance of Alice's favorite password.

(remember we're pretending that Alice has a secure way to send her HASH
during the setup phase, so we ignore how Eve might take advantage of
listening to those messages)

Notice that having Alice hash the passwords ahead of time doesn't make it any
harder for Eve or Ida to get into her account. That's because account access
doesn't actually need the password; it only needs the verifier. Also notice
that the password-recovery work is just as easy as the plaintext-password
case. Bringing back the salt removes the parallelism benefits of running
dictionary attacks against all users at the same time.

Sending Hashed-Salted Verifiers
-------------------------------

Code:
 Setup: Alice picks random 256-bit SALT
        Alice sends SALT, V=HMAC_sha256(SALT,PASSWORD)
        Bob stores salts[ALICE]=SALT, verifiers[ALICE]=V
 Bob: send salts[ALICE] to Alice
 Alice: send V=HMAC_sha256(SALT, PASSWORD)
 Bob: grant access if V == verifiers[ALICE]
Work Needed To Recover Password:
 Wp(Bob): Tsearch * len(dictionary)
 Wp(Eve): Tsearch * len(dictionary)
 Wp(Ida): Tsearch * len(dictionary)
Work Needed To Forge Login:
 Wf(Bob): 0
 Wf(Eve): 0
 Wf(Ida): 0

Adding Iteration
----------------

PBKDF2 is the best-studied member of a class of algorithms named
"Key-Derivation Functions". You use it when you have one key and want to
generate another. It also happens to provide a feature known as "key
stretching" or "key strengthening" (depending on which papers you read),
which basically just adds busywork to the hashing process. The idea is to
increase the amount of time it takes someone to do a dictionary attack. For
PBKDF2, you pick an Iteration Count, and the algorithm takes that many times
longer to run. That makes our scheme look like this:

Code:
 Setup: Alice picks random 256-bit SALT
        Alice chooses iteration count IC, e.g. 10000
        Alice sends IC, SALT, V=PBKDF2(SALT, IC, PASSWORD)
        Bob stores counts[ALICE]=IC, salts[ALICE]=SALT, verifiers[ALICE]=V
 Bob: send salts[ALICE] to Alice
 Alice: remembers previously picked IC
 Alice: send V=PBKDF2(SALT, IC, PASSWORD)
 Bob: grant access if V == verifiers[ALICE]
Work Needed To Recover Password:
 Wp(Bob): Tsearch * len(dictionary) * IC
 Wp(Eve): Tsearch * len(dictionary) * IC
 Wp(Ida): Tsearch * len(dictionary) * IC
Work Needed To Forge Login:
 Wf(Bob): 0
 Wf(Eve): 0
 Wf(Ida): 0
Work Needed To Complete Protocol:
 Wc(Alice): 22us * IC

Now Alice has to do more work to complete the protocol: by making the
attacker's job 10000 times harder, she's also made her own job 10000 times
harder. There's a tradeoff between her convenience and her security: she's
trying to slow down the attackers far enough to make their attack more
expensive than their likely reward.

IC=10000 means Alice will see a 200ms delay during login while her computer
furiously calculates hashes. (Note that Alice has to remember her IC herself:
if she gets it from the server, then a compromised/spoofed server can just
say "IC=1" and bypass all that extra protection).

SHA256 is easy to parallelize, and uses just a few hundred bytes of memory,
which is why a GPU can get such fast aggregate throughput. There are other
key-stretching algorithms that are less friendly to parallelism, specifically
scrypt and bcrypt. These use a lot of memory (specifically memory bandwidth),
exceeding the small storage that each GPU execution pipeline contains. Using
a bcrypt-based KDF prevents the attacker from using cheap fast hardware,
bringing the ratio between Tsearch and Thash closer to 1:1, raising the
attacker's costs further.

Challenge-Response Protocols
============================

So far, Eve has had things easy: Alice reveals everything she needs in the
process of proving her knowledge to Bob. In the web world, we try to hide
this by waving the magic wand of "SSL", which works if 1: the user can
recognize the right site before typing in their password (phishing), and 2:
if the CA system prevents attackers from getting spoofed certificates. It'd
be nice to have a protocol which tolerates eavesdroppers, instead of relying
upon such wishful thinking. Doing this properly requires deep changes to the
web security model, but it can still be educational to see what we might do
if we weren't limited to the web. Certain modes of SSL itself rely upon these
tricks too.

To avoid giving Eve everything, we have to make the protocol more active: Bob
presents a challenge, and Alice uses her knowledge of the password to respond
to it. Each challenge must be different (if Bob re-uses a challenge, Eve can
play back a recorded response). As long as Eve remains a passive observer (no
man-in-the-middle), she doesn't immediately learn the password. She does,
however, learn enough to make some guesses about it.

Code:
 Setup: Bob stores verifiers[ALICE] = PASSWORD
 Bob: sends random 256-bit CHALLENGE to Alice and remembers it for later
 Alice: reponse with ANSWER=HMAC_sha256(PASSWORD, CHALLENGE)
 Bob: grant access if ANSWER==HMAC_sha256(verifiers[ALICE], CHALLENGE)
Work Needed To Recover Password:
 Wp(Bob): 0
 Wp(Eve): Tsearch * len(dictionary)
 Wp(Ida): 0

In this protocol, Eve learns one challenge/response pair. Unless Bob reuses
the same challenge later, this doesn't give her enough information to
directly forge a login. However, this pair *is* enough to give Eve a way
check her guesses: she just walks through all the potential passwords in her
dictionary, runs each through HMAC with the recorded challenge, and compares
the computed response against the one she recorded.

Iterated Challenge-Response
---------------------------

Adding PBKDF2 improves things, but not by a huge amount. Bob is forced to
store the original password, because (like Alice) he must be prepared to
compute the expected response for any arbitrary challenge. Since Bob has to
store the actual passwords, using a salt would provide no benefit. Ida the
intruder, who steals a copy of Bob's database, gets the passwords directly.

Code:
 Setup: Alice chooses iteration count IC, e.g. 10000
        Alice sends IC, PASSWORD
        Bob stores counts[ALICE]=IC, verifiers[ALICE]=PASSWORD
 Bob: send random CHALLENGE to Alice
 Alice: remembers previously picked IC
 Alice: send V=PBKDF2(CHALLENGE, IC, PASSWORD)
 Bob: grant access if V == PBKDF2(CHALLENGE, IC, verifiers[ALICE])
Work Needed To Recover Password:
 Wp(Bob): 0
 Wp(Eve): Tsearch * len(dictionary) * IC
 Wp(Ida): 0
Work Needed To Complete Protocol:
 Wc(Alice): 22us * IC

Asymmetric Cryptography and Zero-Knowledge Proofs
=================================================

SRP
---

There's a tradeoff here: either Bob has to store actual passwords (so Ida has
life easy), or Alice has to send password-equivalents over the wire (so Eve
has life easy). The only way to break out of this zero-sum game is to use
asymmetric cryptography. Both SRP and a public-key-signature
challenge/response scheme allow Bob to store a non-password-equivalent. SRP,
and other PAKE-based systems, allow Alice to start with a password.

SRP in particular allows one side to compute a "Verifier", which can be used
to check a guess, but cannot be used to produce valid guesses itself. Alice
remembers her password, Bob remembers the generated verifier. Alice doesn't
prove her password-knowledge by sending a verifier, instead she proves it by
doing some computation that can be checked by someone who knows the verifier.
This means that Ida's copy of Bob's verifier database doesn't immediately let
her forge logins.

Thanks to some clever math, SRP is a "Zero-Knowledge Proof" for Eve the
eavesdropper. This means that even though Eve sees every messages between
Alice and Bob, she learns no information about the password. Other protocols
might leak partial information about the password (reducing the set of
possibilities with each message), which can eventually give Eve enough
information to guess it. A ZKP gives her absolutely nothing.

Computing the SRP messages takes longer than computing a hash: there are some
very large numbers involved. We'll use "Tsrp" to represent this time. As with
hashing, the user is likely to have a slower implementation than the
attacker.

Code:
 Setup: Alice creates PASSWORD, sends SRP_Verifier(PASSWORD) to Bob
        Bob stores verifiers[ALICE]=SRP_Verifier
 Bob sends SRP challenge
 Alice uses PASSWORD to create SRP response
 Bob checks response against verifiers[ALICE]
Work Needed To Recover Password:
 Wp(Bob): Tsrp * len(dictionary)
 Wp(Eve): infinite
 Wp(Ida): Tsrp * len(dictionary)

Even though the verifier can't be turned directly into a password, Bob and
Ida can still use it to test their guesses. The number of potential passwords
is the only thing standing in their way.

Iterated SRP
------------

To slow down Bob and Ida, we can insert a delay into the process, by doing
iterated hashing (or bcrypt) on the password before feeding it into SRP.

Code:
 Setup: Alice creates PASSWORD, picks IC, computes DERIVED=PBKDF2(PASSWORD,IC)
        Alice sends SRP_Verifier(DERIVED) to Bob
        Bob stores verifiers[ALICE]=SRP_Verifier
 Bob sends SRP challenge
 Alice uses PASSWORD and IC to create DERIVED, then creates SRP response
 Bob checks response against verifiers[ALICE]
Work Needed To Recover Password:
 Wp(Bob): Tsrp * len(dictionary) * IC
 Wp(Eve): infinite
 Wp(Ida): Tsrp * len(dictionary) * IC

Real Improvements
=================

The best way to avoid being vulnerable to any of these characters is to make
the search space so large than it's completely infeasible to test a
significant portion. The "entropy" of the secret is a measure (in bits) of
the attacker's uncertainty. 256 bits of entropy is comfortable safe against
any currently-conceivable non-quantum computer for the practical future. We
wouldn't really use "password" to describe a 256-bit secret, however: we'd
call it a "key", and we'd expect a machine to remember it for us.

 -- example of large password

To avoid other protocol vulnerabilities (in particular the setup phase), an
even better choice is for Alice to construct a public/private keypair, give
the public key to Bob, and then either use it to sign challenges or to
perform a key-agreement protocol. Bob (and Ida) know the public key, but they
come from such a large space that neither can practically deduce the
corresponding private key. This has all the good properties of SRP, but with
enough entropy to ignore the dictionary attack.

This discussion has concentrated on a single interaction that occurs once per
"login". In reality, the login process is a shortcut: what we really care
about is how each individual request is validated. One way to make this kind
of shortcut be secure is to "bind" the shared SSL session key into the login
process: this excludes MitM's by ensuring that both sides agree on the
connection. In some protocols, this can be done by hashing a session
identifier into the messages that are exchanged. Unfortunately SSL
implementations rarely make this identifier available to their clients.


Conclusions
===========

Secrets are vulnerable to guessing attacks, especially when they come from a
small dictionary of possiblities. The protocols used to prove knowledge of
those secrets give attackers material to work with, to test their guesses.
The data that a server records to test these knowledge-proofs can also be
used, either by the server or someone who copies its data, to guess the
password. A well-designed system will minimize the password-guessing power
given to any party, including the server itself.


NOTES
- look up HTTP Basic Auth, associate its modes with these system: RFC2617
 - Basic Auth is really just base64(userid:password)
 - Digest uses KD(secret,value) which is like HMAC but just H(S+V)
  - then A1 = userid:realm:password , A2 = http-method:URI , 
    sends KD( H(A1), nonce:H(A2) )
  - so basically H(H(salt+password)+nonce+URI)
  - so server stores H(salt+password), which is login-equivalent (when
    stolen, it enables someone to login to that site)
- find visual way to express each algorithm and the work functions
- measure SRP speed "Tsrp", both in JS and in attacker's hardware
- show example of 256-bit password
- show entropies of typical passwords
 - picking a single word from a big (235k) dictionary
   (/usr/share/dict/words): 17.8 bits
 - adding three random digits: 27.8 bits
