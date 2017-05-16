Slug: paying-for-storage
Date: 2017-05-15 21:45
Title: paying for storage

Change 'Title', but 'Slug' must match the directory name for images to work
Markdown cheatsheet
Tahoe-LAFS is currently very "grid"-centric. When you set up a client,
you join a specific cluster of machines (based upon an Introducer), and
all your uploads and downloads will only consider those nodes.

I'll tell you a secret: I'm kind of envious of the "one true grid"
properties that a lot of other Tahoe-like projects have:

* "ipfs cat /ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG/readme"
  will get you the README from any [IPFS] node in the world, without any
  pre-arranged server setup or membership steps
* "dat clone
  dat://79cf7ecc9baf627642099542b3714bbef51810da9f541eabb761029969d0161b"
  gets you the current (mutable) copy of a California campaign-finance
  dataset, from any [Dat] client, without naming the servers that are
  hosting the data

In these and other projects, the only setup step is to install the
software. After that, all operations just magically find the right
servers to use, and clients are granted access without any negotiation
or payment. Super smooth.

Of course, the "magic" is hiding a few limitations:

* IPFS and Dat rely upon a DHT to translate the stable cryptographic
  identifiers (the "pubkey names" corner of [Zooko's Triangle]) into the
  current network address of a server that hosts the corresponding data.
* data is hosted by the original publisher and any clients who have
  downloaded a (partial) copy, and who haven't gone out of their way to
  disable sharing of their copies

DHTs and servers depend upon people to run them, and if you aren't
paying someone somehow, then chances are they'll stop doing free work
for you eventually. This works great in the short run, when most of the
people using it are eager and generous, but might suffer as things scale
up. Since Tahoe was originally a *backup* system, reliability remains a
high priority, so we'd prefer to avoid relying too much on the
generosity of unknown strangers.

It's also likely to suffer as things scale *down*. If you're still
paying someone to host your data, but all the pointers are spread
through a DHT, will you still be able to get your data back when the
project's popularity has waned and most of the servers have gone away?

(fun story: as the AllMyData startup machine ground down to a halt, we
had to cut back on our colo bill, which meant throwing out redundant
shares to fit into fewer servers. Eventually all the servers moved into
Peter's basement, and customers couldn't retrieve their files on laundry
day because the 240V outlet was in use by the clothes dryer. Zooko told
me that we should have planned for this and had some tools to gracefully
decommission servers, to consolidate files into a shrinking storage
pool.)

(In addition, neither provides the kind of server-proof confidentiality
that Tahoe offers. Everything in basic IPFS is hashed but not encrypted.
In Tahoe terms, Dat links are basically mutable directory readcaps, but
there are no verifycaps: anyone who can act as a storage servers will
also be able to read the data. Both can be overcome by some extra
protocol work and longer filecaps, the projects just have a different
focus and made different design decisions.)





[IPFS]: https://ipfs.io/
[Dat]: https://datproject.org/
[Zooko's Triangle]: 

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
