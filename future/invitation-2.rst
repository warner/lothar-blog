Relay Server
------------

The relay server provides short-duration (less than 24 hours)
store-and-forward message passing between Alice and Bob (or any other couple
executing the Invitation protocol), implemented as a basic REST-ful HTTP
server. It holds an arbitrary number of "channels", each of which is
identified by a URL that contains the channel's public verifying key (named
``Kchan.pub``). POST messages signed by the corresponding signing key
(``Kchan.priv``) can add messages to the channel or, when the protocol is
complete, delete the channel altogether.

GET to the main URL is used to retrieve the full list of stored messages. For
clients who must fall back to polling, the GET response includes a note about
how long they should wait before asking again (to allow an overloaded server
to throttle clients). It also includes a relative URL to a low-latency
non-polling HTML5 "Server-Sent Events" interface
(http://dev.w3.org/html5/eventsource/), allowing everything but the first
step of the protocol to run as fast as the network allows.

To minimize the DoS-attack window, each channel actually contains two slots
for message-signing-keys. The first is claimed by Alice when she first
creates the channel. The second is claimed by Bob in his first response
message. This prevents an attacker who learns the Invitation data during the
middle of the protocol from injecting messages into the channel and
interrupting the protocol.

The full API is:

* ``CHANNELID`` = ``Kchan.pub``
* ``POST /channels/CHANNELID  json([b64(json({action:"claim-slot", key:b64(slotkey)})), sig_b64, channelkey_b64])``
* ``POST /channels/CHANNELID  json([b64(json({action:"add-message", message: b64(msg)})), sig_b64, slotkey_b64])``
* ``GET /channels/CHANNELID -> json({notes:.., messages:[b64(msg1), b64(msg2), ..]})``
  - 'notes' has ``{pollTime:, eventsURL: "CHANNELID/events"}``
* ``GET /channels/CHANNELID/events`` -> Server-Sent-Events
  - each event is a single line of JSON, no newlines, one message per line
* ``POST /channels/named/CHANNELID  json([b64(json({action:"destroy"})), sig_b64, channelkey_b64])``

The relay server is easy to implement in an event-driven framework like
Twisted or node.js, and can be hosted in any environment where the necessary
Ed25519 verification code can run.


Invitation Size
---------------

So now the protocol details depend upon how large of an Invitation Alice can
afford to hand to Bob. The three basic categories are:

* Large: Alice can email a moderate-sized file to Bob, so the invitation can
  be many kilobytes without hurting usability. Some IM clients can assist
  with file transfers too.
* Medium: Alice can paste a long URL or invitation code to Bob via
  IM/IRC/email, and he can either click on it (activating a browser or custom
  URL-scheme handler) or drag/paste it into his agent. She could also show a
  QR code to his agent's camera. This code is large enough to hold a single
  cryptovalue (256 bits).
* Small: Alice must recite a code-phrase to Bob, either over the phone or in
  person (imagine meeting somebody at lunch and wanting to get their email
  address for later). Bob types it into his agent, possibly with some
  auto-completion assistance. We get maybe 20-50 bits.

Invitation Protocol Details: Large
----------------------------------

When the invitation is large, we can put the entire ``Ealice`` entry into the
invitation itself, along with the coordinates of a relay channel that Bob can
use to respond. When Bob accepts the invitation, his agent puts his ``Ebob``
entry into the relay channel, where Alice's agent can retrieve it and insert
it into her address book.

To make things easy, we encode the invitation data into an image: we take
Alice's user icon (her picture, or avatar, etc), surround it with a frame of
grayscale pixels (in which the invitation is encoded, along with a hash to
guard against image-resizing proxies), and present it in a place where Alice
can drag it into an email message (or IM file-transfer window).

When Bob receives the image, he drags it into his user-agent window, which
extracts the invitation data from the gray pixels. His agent uses the relay
channel to send back the return message.

The invitation data includes a 256-bit random "master secret" named ``MS``.
This is hashed one way to derive ``Kchan.priv``, and a different way to
derive a shared MAC key which Alice and Bob use to recognize each other's
messages.

The actual protocol steps are:

* Alice generates ``MS``, creates the invitation image file (with ``Ealice``
  and ``MS`` in the gray pixels), and offers it to the user for transmission
* Alice derives ``Kchan.priv``, ``Kchan.pub``, and the MAC key.
* Alice allocates the ``Kchan.pub`` channel and fills the first keyslot with
  an arbitrary value (she won't be using it)
* Bob receives the invitation, derives ``Kchan.priv``, ``Kchan.pub``, and the
  MAC key
* Bob adds ``Ealice`` to his address book
* Bob claims the other keyslot with a new random key of his choosing
* Bob creates ``Ebob`` and MACs it, then uses his new slotkey to store the
  message in the channel. Bob is now done.
* Alice GETs Bob's message from the channel, checks the MAC, adds ``Ebob`` to
  her address book.
* Alice uses her ``Kchan.priv`` to destroy the channel, freeing up the
  server's storage space. Alice is now done.

(note that since we need a return channel anyways, we might as well send the
initial ``Ealice`` message through the channel as in the "Medium" case below,
and only put the ``MS`` master secret in the invitation image. This means we
only need to get 256 bits of gray-pixel noise in the avatar icon. That's
about 50 pixels of 40%-60% gray, easily fit into a one-pixel-wide border
around even a tiny 16x16 icon)


Invitation Protocol Details: Medium
-----------------------------------

If the initial invitation can accomodate a 256-bit cryptovalue, then we'll
use it to hold the ``MS`` "master secret" value from the Large case. Alice
will then store her initial ``Ealice`` message in the channel, Bob will
retrieve and check it, then Bob sends his ``Ebob`` message back. The number
of roundtrips is the same, but more data is stored in the channel.

* Alice generates ``MS``
* Alice derives ``Kchan.priv``, ``Kchan.pub``, and the MAC key.
* Alice allocates ``Kchan.pub``, fills the first keyslot with a new random
  key
* Alice creates ``Ealice`` and MACs it, then uses her slotkey to add it to
  the channel
* Alice sends ``MS`` to Bob
* Bob receives the invitation ``MS``, derives ``Kchan.priv``, ``Kchan.pub``,
  and the MAC key
* Bob reads the first message from the channel, checks the MAC, adds
  ``Ealice`` to his address book
* Bob claims the other slotkey with a new random key of his choosing
* Bob creates ``Ebob`` and MACs it, then uses his new slotkey to store the
  message in the channel. Bob is now done.
* Alice GETs Bob's message from the channel, checks the MAC, adds ``Ebob`` to
  her address book.
* Alice uses her ``Kchan.priv`` to destroy the channel, freeing up the
  server's storage space. Alice is now done.


Invitation Protocol Details: Small
-----------------------------------

If the initial chanel is too small to hold a whole 256-bit cryptovalue, then
we can't get full security from a non-interactive protocol. Instead, we add
an extra commitment step, whereby the attacker has an easier guess to make,
but only gets one chance. This protocol, which I'm calling the "Short Secret
String" protocol (although I'm sure I'm just reinventing the wheel and
there's a better name for it out there already), is inspired by the "Short
Authenticated Strings" protocol by Serge Vaudenay (in CRYPTO '05,
http://citeseer.ist.psu.edu/viewdoc/summary?doi=10.1.1.94.8504). It allows
Alice and Bob to exchange arbitrary-sized authenticated (but **public**)
messages, given a short (i.e. weak) secret string. The recipient (either Bob
or the attacker) gets one guess: if they succeed, the messages are exchanged
and both sides can be confident they got the right one, if they fail, the
protocol halts. I'll write up the details of this protocol in a later post.

This results in an extra roundtrip and a few more temporary secrets. It can
also affect how the relay server channel is chosen, because the invitation
code is too short to include a unique channel identifier.

The protocol steps look like this:

* **step 1:**
* Alice generates ``Kchan.priv`` and ``Kchan.pub``
* Alice allocates the channel, fills the first keyslot
* Alice asks the relay server for a "channel discriminator" ``CD``, which
  identifies a small set of channels (it could be just the first few bytes of
  the full ``Kchan.pub`` channel ID, or maybe a small integer). If the server
  is lightly loaded, the set may have just a single channel, but if the
  server is full, the set may contain several channels. There is a tradeoff
  between the length of the discriminator and the number of channels in the
  set, which corresponds to the chances of Bob picking the wrong one and
  wasting both this Invitation and the unrelated one that he tried to claim
  by mistake.
* Alice builds a message ``Ma``, which includes her ``Ealice`` entry, a name
  that Bob will recognize, and her picture/avatar (which Bob might be able to
  pick out from a group).
* Alice generates a long (256-bit) random secret ``Ka``.
* Alice generates a short invitation code ``I``, maybe 10-20 bits
* Alice stores ``Ma`` and ``Ha=H(I+Ka+Ma)`` in the channel
* Alice sends ``I+CD`` to Bob as the invitation code
* **step 2:**
* Bob receives ``I+CD``, asks the relay server for all channels that match
  ``CD``, reads messages from each one, displays the name and picture/avatar
  on a list for Bob to choose from. As the other Invitations are completed
  and their channels are destroyed, this list shrinks. Eventually Bob picks
  one.
* Bob reads and stores (supposed-Alice)'s message as ``Ma2`` and ``Ha2``
* Bob creates his own message ``Mb`` with his ``Ebob`` entry. He also
  generates a long (256-bit) random secret ``Kb``.
* Bob stores ``Mb`` and ``Hb=H(I+Kb+Mb)`` in the channel
* **step 3:**
* Alice reads and stores (supposed-Bob)'s message as ``Mb2`` and ``Hb2``
* Alice sends her ``Ka`` to the channel. (at this point ``I`` effectively
  becomes public: the attacker can use ``Ha`` as an oracle to guess it)
* **step 4:**
* Bob reads and stores (supposed-Alice)'s message as ``Ka2``
* Bob computes ``H(I+Ka2+Ma2)`` and compares against the earlier ``Ha2`` he
  received. If they match, he accepts ``Ma`` as genuine and adds ``Ealice``
  to his address book.
* Bob stores his ``Kb`` in the channel
* **step 5:**
* Alice reads (supposed-Bob)'s message as ``Kb2``
* Alice computes ``H(I+Kb2+Mb2)`` and compares against the earlier ``Hb2``
  she received. If they match, she accepts ``Mb`` as genuine and adds
  ``Ebob`` to her address book.

The SSS protocol works because the attacker has to commit to a message before
they've learned enough to effectively guess the unknown secret I. Suppose
Mallory is trying to claim the invitation for herself (she wins if Alice
thinks she's added Bob's data to her address book, when in fact she's added
Mallory's). Mallory needs to store her own message ``Mb=Mk`` in step 2, and
at the same time she must pick an ``Hk`` to send in place of Bob's ``Hb``. As
an MitM she knows ``Mb``, but she doesn't know ``I`` or the real ``Kb`` yet,
and (because ``Kb`` is long) knowing Bob's ``Hb`` is insufficient to let her
guess them. So the best she can do is pick a random ``Kk`` and guess at ``I``
(call her guess ``Ik``), and build ``Hk=H(Ik+Kk+Mk)``. Later, by step 4, she
knows both ``Ka`` and ``Kb``, which lets her guess the real ``I``, and she
finds out whether her guess was right. She can choose whatever ``Kk`` to
reveal that she likes, but if her guess was wrong, it's infeasible to find a
new ``Kk2`` that allows ``H(I+Kk2+Mk)`` to equal the previously-committed-to
``H(Ik+Kk+Mk)``, so Alice won't accept her message and the protocol stops.
(As David-Sarah Hopwood pointed out, it's important for this H hash to resist
length-extension attacks, but that's pretty easy).

The worst problem I can think of so far is the asymmetry: Mallory learns that
she guessed wrong before Alice gets the last message, so she can fake a
network problem and run away. Alice cannot distinguish between a network
problem and a failed guess, so she might be willing to just try again, when
in fact she's under active attack and should fall back to something more
secure.

In practice, the invitation's "code phrase" ``I+CD`` would be expressed as a
series of words chosen from categories with maybe 1024 entries each.
Something like COLOR-ANIMAL-ACTIVITY could result in comical easy-to-read
sequences with a moderate amount of entropy. The receiving code can do
auto-completion from the same wordlists, so Bob only has to type a few
letters for each one.

When Bob tells his agent to accept an incoming Invitation, channel contention
may mean Bob has to pick among several potential Invitations. By putting
Alice's name and image on the channel, Bob's agent can show him a list of
pending invitations and ask him to claim one. If he picks the wrong one,
he'll effectively be attacking somebody else's invitation, and Alice's will
expire unused. As other users claim their own invitations, their channels
will be closed, so if Bob is lazy he can just wait until the number of
remaining options drops to one. (of course, if some other user is similarly
lazy, the remaining options will drop to two, and eventually somebody must
make a decision). There may be other criteria to help him pick the right one:
for QR-code -based face-to-face interactions over lunch, we can rule out any
invitation that originates from more than 10 feet away.

There is a multi-way tradeoff between number of words Alice must recite, the
security (length) of ``I``, the length of the channel-discriminator ``CD``,
the number of options Bob must choose between, and the attacker's chance of
guessing I correctly and thus stealing the invitation. This is also related
to the total number of users sharing the same relay server, their rate of
issuing new invitations, the average time for which each invitation remains
outstanding, the frequency with which attackers try to steal invitations, and
the maximum acceptable rate of successful attacks. We might also be able to
do some work on the relay server (to notice lots of claims coming from a
small number of IP addresses, or add a CAPTCHA) to raise the cost of
large-scale attacks.

I'll examine the numbers here in a later post, but my general sense is that
small systems (like Tahoe) can use 10-bit code-phrases safely, while popular
systems (like anything which managed to ship in a browser) with millions of
users might need 30 bits to be safe. A target of "average duration between
successful attacks must be >10 years" might be reasonable.

We can also be adaptive: offer the short code-phrase approach unless the
server tells us there are too many channels in use (or too many attacks
taking place) to safely use short phrases, then apologize to the user and
tell them to paste a medium-size invitation code instead. Or use the
less-secure approach but then require confirmation from a post-negotiation
verification step (negotiate a shared secret and show it to both users for
comparison). Occasional re-keying (negotiating new keys in a channel secured
by the old ones) can also help, as it obligates the successful attacker to
continue their MitM role at all times: if they ever miss a re-keying
operation, they'll be locked out forevermore.

I'm slowly starting to implement this scheme, as a set of python functions
and a relay server. Eventually I'll assemble some mockups of what the "Invite
A Friend" and "Accept An Invitation" dialogs would look like. I'm looking for
feedback about the protocol and the overall usability. Let me know what you
think!
