Slug: 53-petmail-delivery
Date: 2015-07-25 16:38
Title: Petmail mailbox-server delivery protocol

[Petmail](https://github.com/warner/petmail) senders use a
"[Mailbox server](https://github.com/warner/petmail/blob/48a712d8b0b6556dd608fbcb1d05178270ef3a8f/docs/mailbox.md)"
to queue encrypted messages when their recipient is offline (and even when
they aren't). The recipient might pick up the message right away, or might
not learn about it until later. These mailboxes need a way to tell whether
they should spend their precious disk space to queue an incoming message, or
if it's just unwanted spam. The "delivery protocol" must convey enough
information for the mailbox server to make this decision.

We have several potential security goals for this delivery protocol,
categorized as follows (in each case, "0" is the best):

For the sender S:

* S0: two different senders cannot tell if they're talking to the same
  recipient or not
* S1: they can, by comparing their keys and delivery tokens.

(when I started Petmail, I thought S0 was important, but I've since changed
my mind, and these days I'm not trying so hard to achieve it)

For the mailbox server M:

* M0: the mailbox server cannot tell which message came from which sender,
  not even that two messages came from the same sender, nor can it determine
  how many senders might be configured for each recipient
* M1: the server cannot correlate messages with senders (or each other), but
  **is** able to count (or at least estimate) how many senders ther are per
  server
* M2: the server can correlate messages with each other, or with a specific
  (pseudonymous) sender, and by extension can count senders too

For the recipient R:

* R0: the recipient can use the transport information to accurately identify
  the sender
* R1: they cannot: the recipient depends upon information not visible to the
  mailbox server to identify the sender, which means a legitimate (but
  annoying) sender could flood the server without revealing which sender they
  are

And the revocation behavior:

* Rev0: R can revoke one sender without involving the remaining ones
* Rev1: if R revokes one sender, they must somehow update all other senders
  with new information

Other design criteria include the amount of state that must be managed by the
mailbox for each recipient, and the computational and cryptographic
complexity of the protocol.

## Security Properties of Existing Delivery Protocols

For example, a simple no-frills non-anonymous protocol would publically sign
each message with a constant (per-sender) signing key, and would include a
constant per-recipient queue id. The mailbox server could hold a list of
approved senders for each recipient. This would achieve "S1 M2 R0 Rev0":
minimal anonymity, but very easy to implement, and revocations are trivial
(just remove the bad sender from the approved list).

Petmail's current protocol uses re-randomizable delivery tokens (the
implementation is currently a simulated stub, but the math is pretty easy to
do properly). This uses an encryption scheme in which anyone with the right
pubkey can re-encrypt a token into a new one, and nobody can correlate the
two except for the privkey holder, who can decrypt both to the same
plaintext. The mailbox server allocates the plaintext token for each
recipient, and holds the private key. The recipient randomizes a new token
for each sender, and the sender re-randomizes their token for each message.
This achieves "S0 M0 R1 Rev1". The annoying "R1" means that the recipient
depends upon a second field, encrypted out of reach of the mailbox server, to
determine who sent the message. This means that a malicious sender can flood
the mailbox with messages the recipient cannot attribute to a specific
sender, so R won't know which S to revoke. Apart from this defect, the
anonymity properties are ideal, and the implementation complexity is
moderate. The mailbox state for each recipient is minimal (one token, one
private key). However the revocation process requires allocating a new token
and updating the remaining senders, which is racy and can deanonymize senders
who are blocked from hearing about the new token.

[Pond](https://pond.imperialviolet.org/)'s original protocol used BBS group
signatures, and achieves "S1 M0 R0 Rev1". The "S1" results from each sender
getting the same (group) public key, so senders can trivially compare keys to
confirm that they're talking to the same recipient. The improved "R0" results
from the group signatures: the same signature that allows the mailbox to
confirm group membership also allows the recipient to identify the specific
sender, so they know which sender needs to be revoked. Unfortunately the
cryptographic complexity is higher (fancy math), and the revocation story is
similarly tricky. I've heard that Pond will abandon the group signature
scheme in favor of a simpler "stash of tokens" approach, but I haven't seen
any details.

## Delivery+Decrypt Tokens

Recently, on the
[messaging](https://moderncrypto.org/mail-archive/messaging/) list, we've
[discussed](https://moderncrypto.org/mail-archive/messaging/2015/001769.html)
how the delivery identifiers could interact with forward-security key
rotation. The simplest scheme I can think of would assume that keypairs are
cheap (yay Curve25519!) and replace an interactive two-key ratchet (updated
once per roundtrip) with an (interactive) explicit list of single-use
pubkeys. It would look like this:

* Recipient maintains a set of a few thousand Curve25519 keypairs. For each
  one, they derive privkey -> pubkey -> HMAC key -> HKID (mostly by hashing),
  and remember a table that maps HKID->(senderid, privkey). Each is
  single-use, and it creates more to replace them as they get used up.
* Recipient gives the HMAC keys to the Mailbox server, keeping it up-to-date
  as new ones are created. M maintains a table mapping HKID->(HMAC key,
  recipient).
* Recipient gives some pubkeys to each sender, keeping them stocked with
  maybe 20 at a time.
* Each time the sender creates a message, they derive the HMAC key and HKID,
  encrypt their message (with an ephemeral Curve25519 keypair, attaching the
  ephemeral pubkey to the message), append the HMAC tag, prepend the HKID,
  then send the result to the mailbox server. The mailbox looks up the HKID
  to get the HMAC key, validates the HMAC, and enqueues the whole message to
  the recipient. The recipient fetches the queued messages, looks up the HKID
  to find the sender and privkey, derives and validates the HMAC, then
  decrypts the message and destroys the (HKID, privkey) pair.

This protocol achieves "S0 M1 R0 Rev0". We fail to get "M0" because the
mailbox can count outstanding tokens to estimate how many senders can send to
each recipient (although we can hide moderate numbers of senders pretty
easily). But otherwise it's ideal. The forward-security window (during which
a recipient state compromise reveals old messages) is absolutely as small as
possible: each private key can be destroyed as soon as the message is
received/decrypted. Revocation is trivial (just stop making new tokens), and
can probably be sped up by cancelling the outstanding ones. Traffic whitening
(so make each message uniformly random) could be achieved with Elligator, or
by deriving a symmetric key from each token and using it to encrypt the
ephemeral pubkey.

One downside is the storage space that mailbox servers must dedicate to these
tokens. Imagine 1000 recipients using the same server, each of which has 500
senders, with 20 tokens each: that's 10M tokens. But the HMAC keys don't need
to be particularly strong, as they're protecting server space, not
confidentiality. And we can afford a few collisions in the HKID values too,
since the mailbox can trial-verify against multiple tokens. 128-bit HMAC keys
and 32-bit HKID values give you 20 bytes per token (and one HKID collision
per 1000 messages), so 10M tokens would require 200MB of space on the mailbox
server, plus the actual messages that it's getting paid to queue.

Using HMAC (instead of Ed25519) means the mailbox server can create its own
tags and mix-and-match messages with tokens, but they'll just be dropped when
the subsequent Curve25519 decrypt fails, and M already has the ability to
destroy arbitrary messages. It might be appropriate for R to ignore the HMAC
tag, and just treat HKID as a hint to avoid expensive trial-decryption.

Another minor downside is the interaction necessary to update both senders
and the mailbox server. We should probably amortize the updates: deliver
tokens to the mailbox in batches of 100, and to senders in batches of 5. Each
message should tell the receiving agent how many tokens the sender has left
(to tolerate lost messages better), and we might want a special mailbox
channel (not managed by tokens) to simply say "help! send more tokens!".

But the most significant downside is the "fail-stop" behavior of an offline
recipient. If your agent doesn't pick up messages frequently enough, a busy
sender can run out of tokens, and then they can't send you new messages until
you collect the old ones (and deliver more tokens). This behaves more like a
full voice-mail-box than an email server (except the limit is per-sender
rather than per-recipient). It's not necessarily a bad constraint on
individual human senders, but would be particularly annoying for aggregated
mailing lists or automated/machine-generated messages.

## Design Choices

I think the last issue is unavoidable for protocols that use per-message
tokens. We basically have three design options, each with its own problems.
The mailbox server can either recognize:

* one thing per message (tokens): fail-stop on exhaustion
* one thing per sender (public signatures): not sender-anonymous
* one thing per recipient (group signatures or re-randomizable tokens):
  hard to revoke a sender


Or recognize nothing, accept all messages, and be vulnerable to DoS attacks
(not exactly spam, since the end user never sees it, but there won't be
server space left for the desired messages).

I think I'm going to prototype the one-token-per-message approach for Petmail
and see how it works out. I kind of like the current re-randomizable tokens
scheme, but I'm a bit worried about the unidentifiable junk-mail problem, and
per-message tokens are the only clean way I can see to avoid it.

This is definitely very "chatty": lots of little messages are being sent, in
the interests of preventing the wrong big messages from being delivered (as
well as providing forward-security).
