Slug: 52-linkability
Date: 2014-09-27 09:25
Title: Anonymity, Pseudonyms, and Linkability

## Linkability

Communication systems can be evaluated on how much *linkability* they offer (or withhold) between different aspects of one's identity.

At one extreme, a face-to-face conversation with your long-term friend provides extremely strong linkability between two things. One is your conception of them: the idea in your head that points at them, something like "my old college friend Phil", along with all the feelings and memories you associated with them, the sound of their voice, the image of their face, and the tenor of their thoughts. The other is the words that you're hearing from them. You can be really confident that *those* words, and no others, are being produced by *that* person, and no other.

At the other extreme, a typewritten note in machine-translated english printed in a neutral font on untraceable paper, slipped under your door while nobody is looking and you were away on vacation for a month, is pretty much unlinkable to anything else. And if you're the sort of person who regularly receives such messages (perhaps you're a detective/journalist known for accepting anonymous tips), then a second one arriving under the door might or might not have anything to do with the first. We might say the message is unlinked even from the method of delivery.

## Identity

As a basic goal, we usually want the recipient to be able to link each incoming message to some sender's "identity", which includes such notions as:

* how did we meet?
* our reasons for talking to them
* private things we think about them
* who do we think they are?
* our conversation history: the messages we've exchanged back and forth with them

This history includes the correspondent's claimed name: frequently, the first message we receive from a new sender starts with "Hi, my name is XYZ". The French equivalent, "Je m'appelle XYZ", is literally translated as "I call myself XYZ".

We might believe that other people are conversing with the same person as we are, and the use of cryptographically signed messages might even prove it. In this case, we can add another piece:

* what other people have said about them to us

All the other forms of a "name" fall into this category. When Bob tells you "I have this friend named Zooko, I think you'd find him really interesting", creates a slot in your brain that's labelled "the guy that Bob calls Zooko", and bound with "Bob thinks you'd find him really interesting", and if you're lucky enough, this mental database row will eventually bound to your future interesting conversation with him.

This includes ideas like "official identity". A drivers license binds together a picture, a name, a birthdate, and a home address, with all the strength (or lack thereof) of a large-scale overworked government department with the moral and legal authority to throw counterfeiters in jail. 

We almost always label these collections of identity notions with a name of some sort. People we meet in IRC chat rooms tend to get labelled with a screen name, then the entries get populated with our observations of their personalities and skills. Later, if we meet them in real life, we might bind this identity to a face and a voice, or with a "real name".

And notably, the same human being might be bound to multiple identities, even within the same "identity database". You might read John's blog post that he prefaces with "speaking only for myself, not on behalf of my employer", and then see him cited as the spokesperson for the organization in a more official communication. These are, at least nominally, two separate identity "slots" for the same person, pointing to each other but ideally distinct.

## Relationship Hiding

## Anonymity

"Sender Anonymity" frequently means that the recipient of a message doesn't know very much about the person who sent it.

The typical example of sender anonymity is the "anonymous tip": a message (reporting a crime), sent to a well-known figure, hides the sender's public identity to protect them from reprisals. This is the mode provided by most anonymity systems.

"Receiver Anonymity" means the sender doesn't know who they're sending the message too, even though the recipient might learn who the message is coming *from*. It rarely means **no** knowledge (yelling at random strangers is not a conversation per se). More typically the sender has some idea or concept of "who" they're talking to (like "the guys who run Wikileaks", or "the author of that intriguing-yet-scandalous essay I read yesterday"), but are unable to learn more conventional aspects of the recipient's identity like a birth name, address of residence, name of employer, IP address, or what other scandalous essay's they've written under different pseudonyms. Any of these might be used to harm the recipient (even if the IP address doesn't reveal a location, it subjects them to a DoS attack).

Receiver anonymity is less common. The most obvious example is when the police televise an appeal on the local news, asking for "anyone who has information on this crime to please call XYZ". Anyone watching TV that night will get the message.

It is rare for this to include confidentiality too (if you can't name the intended recipient, it's hard to arrange for them to be the only person who can read it), but one use case comes to mind: there may be a secure reply channel to the *sender* of an sender-anonymous tip. In SecureDrop, for example, the journalist who receives a message can respond to the sender, knowing that only the original sender (who possesses a secret key) can see the response. This property derives from Tor (senders use Tor to connect to a SecureDrop server) and it's low-latency onion-routed network, which provides a reverse channel for each connection.

High-latency mix networks typically do not provide such a reverse channel, requiring other tools to enable two-way communications. More in a later blog post.



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
