:title: Promises
:date: 2006-09-23 10:25
:category: twisted
:slug: 23-promises

Aaaagh! Promises are hurting my brain.

I'm trying to figure out how to provide a useful subset of E's `reference
mechanics <http://www.erights.org/elib/concurrency/refmech.html>`__ in
newpb/`foolscap <http://twistedmatrix.com/trac/wiki/FoolsCap>`__.
Specifically, one of the clever things that E does is to provide `Promise
Pipelining <http://www.erights.org/elib/distrib/pipeline.html>`__, a limited
form of remote code execution, in which I can ask you for an object and tell
you to deliver a message to that object in a single round trip (rather than
the usual two). So I want to be able to do something like::

 # target, record, and results are all Promise objects
 target = tub.getReferenceAsPromise(sturdyref)
 record = send(target).getRecord(args)
 results = send(record).getField(otherargs)
 def printResults(r):
   print r
 when(results).addCallback(printResults) # when() returns a Deferred

You can also include Promises as arguments::

 record = send(target).getRecord(args)
 send(laserprinter).printRecord(record)

So I'd like to provide this feature in python/foolscap, both because using
Promises as a programming technique holds a lot of promise (as it were) for
being a cleaner asynchronous style, and because it opens up the possibility
of doing pipelining (which is an actual performance win).

The challenge is that E has very different reference mechanics than python.
In E, **any** reference could be a Promise. (specifically, each reference is
in any one of `5 states
<http://www.erights.org/elib/concurrency/refmech.html>`__: LocalPromise,
RemotePromise, Near, Far, and Broken). Whereas in python, references are
always Near, and we have to fake everything else with wrapper objects.

My current approach is to have the Promise class be the wrapper and have it
handle everything except Near references. The basic Promise is created with a
matching resolver::

 promise, resolver = foolscap.makePromise()
 resolver(result) # resolves the promise

But the most common way to get one is to do an eventual send to something::

 from foolscap import send
 class Adder:
   def add(arg):
     return arg+1
 a = Adder()
 promise = send(a).add(4)

There are only two things you can do with a promise: send it more messages,
and wait for it to resolve. The former is done with ``send`` (which accepts
either a promise or a regular object, and **always** does an eventual-send),
the latter is done with ``when``::

 from foolscap import when
 d = when(promise)
 d.addCallback(printResults)

The ``when`` always returns a Deferred that will fire with the
resolution of the Promise. So ``send`` moves us from the synchronous
world to the asynchronous+promise world, while ``when`` and
``addCallback`` move us back to the synchronous one. (``when`` by
itself moves us from the asynchronous+promise world to the
asynchronous+Deferred world).

So far so good. But here are some problems:

- can Promises be resolved multiple times? I don't think so. The state
  transitions between LocalPromise and RemotePromise don't count.

- how should this interact with eventual-send? certainly when you do
  ``send(a).foo()``, and a is a normal reference (not a Promise), that
  ``a.foo()`` call should not happen in the same call stack (i.e. Vat
  turn, i.e. Reactor tick). But should all the events be sent in a big batch
  as soon as the promise is resolved? Or should they be sent out one at a time
  somehow? I suppose if Promises can only ever be resolved once, this is not
  as complicated as I'd first thought.

- Should we try to support immediate calls to resolved Promises? In E, if
  you have a Near reference, you can do both immediate and eventual sends. In
  python, it would look like:

::

 p = send(obj).foo(args)
 # later.. p is probably resolved
 send(p).bar() # eventual send
 p.baz() # immediate send

Hm, maybe that isn't such a great idea.
