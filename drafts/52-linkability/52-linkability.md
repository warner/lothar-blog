Slug: 52-linkability
Date: 2015-06-01 14:10
Title: Anonymity, Pseudonyms, and Linkability
Category: petmail

## Linkability

!BEGIN-SUMMARY!
Communication systems can be evaluated on how much *linkability* they offer (or attempt to conceal) between different aspects of one's identity.
!END-SUMMARY!

At one extreme, a face-to-face conversation with your long-term friend provides extremely strong linkability between two things. One is your conception of them: the idea in your head that points at them, something like "my old college friend Phil", along with all the feelings and memories you associated with them, the sound of their voice, the image of their face, and the tenor of their thoughts. The other is the words that you're hearing from them. You can be really confident that *those* words, and no others, are being produced by *that* person, and no other.

At the other extreme, a typewritten note in machine-translated english on untraceable paper, slipped under your door while nobody was looking and you were away on vacation for a month, is pretty much unlinkable to anything else. And if you're the sort of person who regularly receives such messages (perhaps you're a detective or journalist known for accepting anonymous tips), then a second one arriving under the door might or might not have anything to do with the first. We might say the message is unlinked even from the method of delivery.

## Identity and Pseudonyms

As a basic goal, we usually want the recipient to be able to link each incoming message to some sender's "identity", which includes such notions as:

* how did we meet?
* our reasons for talking to them
* private things we think about them
* who do we think they are?
* our conversation history: the messages we've exchanged back and forth with them

This history includes the correspondent's claimed name: frequently, the first message we receive from a new sender starts with "Hi, my name is XYZ". The French equivalent, "Je m'appelle XYZ", is literally translated as "I call myself XYZ".

Perhaps we believe that other people are conversing with the same person; the use of cryptographically signed messages might even prove it. In this case, we can add another piece:

* what other people have told us about them

All the other forms of a "name" fall into this category. When Brian tells you "I have this friend named Zooko, I think you'd find him really interesting", this creates a slot in your brain that's labeled "the guy that Brian calls Zooko", and bound with a note that says "Brian thinks you'd find him really interesting". And if you're lucky enough to meet Zooko, this mental database row will eventually get bound to your future interesting conversations with him.

This includes ideas like "official identity". A drivers license binds together a picture, a name, a birthdate, a home address, and the implied-positive results of a driving test, with all the strength (or lack thereof) of a large-scale overworked bureaucratic government department with the moral and legal authority to throw counterfeiters in jail. 

We almost always label these collections of identity notions with a name of some sort. People we meet in IRC chat rooms tend to get labeled with a screen name, then the entries get populated with our observations of their personalities and skills. Later, if we meet them in real life, we might bind this identity to a face and a voice, or with a "real name".

If this name is carefully never associated with a "real world" identity, and is cultivated to give it a long-term life of its own, we call it a "pseudonym".

And notably, the same human being might be bound to multiple identities, even within the same "identity database". You might read John's blog post that he prefaces with "speaking only for myself, not on behalf of my employer", and then later see him cited as the spokesperson for the organization in a more official communication. These are, at least nominally, two separate identity "slots" for the same person, cross-referenced but ideally distinct.

## Flavors of Anonymity

"Sender Anonymity" frequently means that the recipient of a message doesn't know very much about the person who sent it. An "anonymous tip" is the usual example: the tipster sends a message (reporting a crime) to a well-known figure (the police). Everyone knows who the recipient is, but the system hides the sender's public identity to protect them from reprisals. This is what most systems mean when they claim to provide some sort of anonymity.

"Receiver Anonymity" means the *sender* doesn't know who they're sending the message *to*, even though the recipient might learn who the message is coming *from*. It rarely means **no** knowledge: yelling at random strangers is not a conversation per se. More commonly the sender has some vague idea or concept of "who" they're talking to (like "the people who run Wikileaks", or "the author of that intriguing-yet-scandalous essay I read yesterday", or Batman), but are unable to learn more conventional aspects of the recipient's identity like a birth name, address of residence, name of employer, IP address, or a list of what other scandalous essays they've written under different pseudonyms. Any of these might be used to harm the recipient (even when the IP address doesn't reveal a location, it subjects them to a DoS attack).

Receiver anonymity is less common. One example is when the police televise an appeal on the local news, asking for "anyone who has information on this crime to please call XYZ". Anyone watching TV that night will get the message, and the police won't know who they are (until they call). Commissioner Gordon doesn't know where Batman lives, but when he shines a bat-shaped spotlight into the clouds, the caped crusader will get the message.
 
These examples hint at a deeper property: to use either form of anonymity in a practical (bidirectional) communication system, you must generally have a "reverse channel" of some sort. Sender anonymity without a way to get messages back to the sender is pretty unsatisfying: it might useful for delivering praise or anger, but not for having an actual conversation. Receiver anonymity without a response pathway would leave Batman wondering who, exactly, needs his help: fortunately for the comic books, there's only one Bat-Signal.

[Tor](https://www.torproject.org/), because it is low-latency and circuit-based, makes this reverse channel easy, at least while the sender is delivering a message. High-latency mix networks typically do not provide such a reverse channel, requiring nymservers and other tools to enable two-way communication. And achieving both sender- and receiver- anonymity, at the same time, needs even more work. More on this in a later blog post.

Finally, note that it is rare for receiver-anonymous systems to include confidentiality too: if you can't name the intended recipient, it's hard to hide your message from everyone else. All of Gotham knows when the Bat-Signal is activated. But this *can* be achieved if the recipient's public identity includes a public encryption key. In the ideal system, this pubkey is the only thing we learn about the recipient.

## Relationship Hiding

One other aspect of identity is the relationship: who else are they talking to? This might be revealed by reading the headers or routing information from a message, or by watching the network traffic of one or both ends to see where the packets are going (and then associating an IP address with other aspects of their identity). Even if you run all your connections over Tor, there are other subtle clues available to the attacker: correlation between timing of network activity (without IP addresses), public behavior provoked by information being revealed (imagine a [subtle disinformation campaign](http://tvtropes.org/pmwiki/pmwiki.php/Main/FeedTheMole) used to reveal a leak), or merely the act of using a computer at the same time as someone else.

Some of these attacks can reveal a hidden correspondent ("who is Alice talking to?"), others are better at confirming or denying the potential connection between two known correspondents ("is Alice talking to Bob?"). And some require access to network traffic in multiple places: the two participant's computers, intermediate servers, or other potential correspondents.

And if intermediate servers are used (perhaps to queue inbound messages while the recipient is offline), there may be administrative or financial connections between the recipient and the server that could be revealed.

## Unlinkability is Hard

Unlinkability is a noble goal, but it's hard. Most of the secure messaging systems currently in development don't even try (with [Pond](https://pond.imperialviolet.org) being the notable exception).

Running all connections over Tor (and using Hidden Services for listening sockets) hides IP addresses from direct observers. But it costs: higher setup complexity, increased connection latency, and reduced throughput. We need to ship a Tor binary in our packages, or require users to install one on their own. It also excludes some interesting use cases that I want to explore, like publishing "one-to-everybody" data to the entire world.

No (practical) systems are secure against a "global passive adversary", but it's possible to hide timing correlations against weaker eavesdroppers who can only observe a subset of the machines. Pond does this by using randomized constant-rate access patterns for message delivery and retrieval. The downside that it's very slow: Pond sends/receives an average of 16KiB every 5 minutes, which is 55 *bytes* per second. That's fine for email (I certainly can't type any faster than that), but would be frustrating for larger uses (Pond has a separate scheme for large attachments, but it's clearly marked as providing less anonymity).

Using a recipient-side "mailbox" server presents another challenge. You need one to let you receive messages even when your computer is offline, but *somebody* has to manage (and pay for) that server. You can run or rent your own server, but buying server time or rack space anonymously is not very easy. Borrowing space from a friend implies a link between you two, which could be traced. AGL offers a Pond server for free use, but that won't scale if it becomes popular.

The final challenge lies in the invitation protocol by which two new users connect for the first time. This requires a server too, and timing correlations between key-exchange messages can be used to link users before they've sent their first real message.

## What To Include In Petmail?


I've been trying to decide what sorts of anonymity to include in Petmail. I like the deployment path of a locally-hosted web-app, which basically rules out Tor (until it gets embedded directly into the browser, wouldn't that be cool?). That would let us leverage the WebRTC code that's in modern browsers to establish point-to-point connections between online agents for file-transfer and realtime chat, but that reveals IP addresses all over the place.

On the other hand, using Tor gets you NAT-traversal for free (via hidden servers), and it's at least theoretically possible to bundle a Tor daemon along with a larger app (instead of asking the user to install one themselves). [txtorcon](https://txtorcon.readthedocs.org/en/latest/) makes it pretty easy to launch and publish a hidden-service port.

I'm not sure where Petmail will go. It's unfortunate that unlinkability (like security) really needs to designed-in up-front. It's not the kind of thing you can bolt on later, so it has the potential to hold up the rest of a project. I may hack on the other communication features first, to get a sense of what the possibilities are, and then circle back around to anonymity issues (and redesign a lot of stuff).


(many thanks to Nick Sullivan for reviews and suggestions)
