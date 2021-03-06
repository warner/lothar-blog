:title: Twist-E
:date: 2005-05-27 18:00
:category: twisted
:slug: 15-Twist-E

Spent another great day down at HP, talking about implementing E and
web-calculus concepts within Twisted and newpb. `Tyler Close
<http://www.waterken.com>`__ was kind enough to spend the entire afternoon
with me, explaining how his `web-calculus
<http://www.waterken.com/dev/Web/>`__ works and the design decisions behind
it. I'm really excited about implenting this stuff in newpb: I think we can
make a system that's both secure *and* highly usable. Some of the ideas I
came away with that I want write up before I forget:

Promises: In addition to Deferred, we can build a Promise. The usage syntax
would look like::

 p = tub.getReference(url)
 p.authorize(credentials).subscribe(self)
 when(p.getReady()).addCallback(lambda res: p.trigger())
 p2 = Promise(d1) # turn "deferred which fires with an instance" into a Promise
 p3 = p2.invoke()
 d2 = when(p3)
 d2.addCallback(stuff)

The Promise object is basically a wrapper around any Deferred that expects to
fire with an instance. It has a __getattr__ which lets it pretend to
implement any method. Such methods just queue the call and its arguments,
then finish immediately, returning a new Promise. Something like::

 class Promise:
   def __getattr__(self, methname):
     if self.resolved:
         m = getattr(self.resolution, methname)
         assert callable(m)
         return m
     def newmethod(*args, **kwargs):
         self.calls.append((methname, args, kwargs))
         # except more cleverness in case the method is invoked after the
         # promise is resolved
     return newmethod

When the Deferred fires, all pending calls are invoked on the instance it
fired with. Each call also returns a Promise, possibly already fulfilled,
with the results of that call, so that ``p.meth1().meth2()`` is the
asynchronous equivalent of ``o.meth1().meth2()``, or
``func2(func1(o))``. '``p.meth1(); p.meth2()``' means that meth2
must be invoked *after* meth1: I'm not sure what other kind of sequencing
promises to make (should we wait until meth1 has finished before invoking
meth2?).

If the Deferred errbacks instead, then the Promise is "smashed", which is
like an errback. No further method calls are made, any dependent Promises are
smashed too.

The idea is to make the asynchronous domain be the normal case, and mark the
boundary with the synchronous domain specially. ``when()`` would be a
function that turns a Promise into a Deferred, with which the transition
could be scheduled::

 def when(p):
   if not isinstance(p, Promise):
     return defer.succeed(p.resolution)
   if p.resolved:
     return defer.succeed(p.resolution)
   else:
     d = defer.Deferred()
     p.waiting.append(d)
     return d

He pointed out that E currently has two separate method invocation syntaxes:
'o.foo()' requires a local reference, and may or may not return a Promise. 'p
<- foo()' can accept either a local reference or a Promise, and always
returns a Promise. (actually I'm not sure I'm getting this right, but the
implication was that there were two forms, one for local and one for remote,
whereas Tyler felt that there should only be one).

Then, later, we'll create the RemotePromise, which is a Promise that's
associated with a RemoteReference. ``rp.foo(args)`` is equivalent to
``d.addCallback(lambda res: res.callRemote("foo", args))`` . When
Promises are serialized, they get a clid and show up as another Promises on
the far end. You push the waiting as far away as possible, apparently this is
the way to reduce the probability of deadlocks.

My main concern with this syntax is that it may confuse the
synchronous-domain developers that we (as Twisted) have been trying to gently
nudge into the world of asynchronous programming. We're not blocking, but the
code looks a lot like that's what's happening. But, once you've stopped
thinking that the lack of a ``.callLater`` implies immediate execution,
the ``p.meth(args)`` syntax really is a lot cleaner. You just assume
that **everything** could be a promise, and you use ``when()`` if you
need to assure that you have an immediate value.

One problem with reference counting is that your peer can force you to retain
an object for arbitrarily long times, by just never sending you the decref
(and Gifts make things even worse). Tyler's hunch is that distributed
reference counting is the wrong approach, and it is more practical to manage
object lifetime with the Vat/Tub. Break application processing into units,
create a Tub for each unit, when the unit is finished, destroy the Tub. All
objects that pass through a Tub are registered (under an unguessable name) in
that Tub, so they remain accessible for the lifetime of the Tub, and then
become inaccessible when the Tub is destroyed.

To use this well, it must be easy to create new Tubs and destroy them later.
These Tubs must be able to share listener ports, which can distinguish the
desired Tub by its keyid. To accomplish this with newpb, I think we may need
a module-level registry of Listeners, so that two Tubs that are asked to
listen on the same port will register with the same Listener. (it might also
make sense to use ``newtub = oldtub.makeTub()``, and have the Listener
be inherited). We should pay attention to the possibility of sharing a TCP
connection to an existing Tub, but keep in mind that separate TLS keys will
require separate TCP connections.

Secure PB URLs want a key as the primary specifier, followed by a list of
location hints, followed by a Tub-scoped name::

 PBY url: pby://key@1.2.3.4,foo.com,[::1],loc2,loc3/name
  key is base32(sha1(tub.pubkey))
  unix socket is trickier
  non-authenticated url still requires Tub ID

He also feels that DoS prevention (one of the three reasons for Constraints,
the other two being semantic typechecking assertions and API documentation)
is difficult to implement and hard to get right, and unlikely to do the
complete job that you'd want out of it. He said MarkM burned a lot of cycles
trying to build DoS prevention techniques into CapIDL, and it would be worth
asking him for his thoughts.

He said one deployment pattern would be to put security proxies in a set of
separate processes, which perform deserialization, check arguments, etc, and
then pass the results on to the real object. The security proxies would be
CPU/memory limited, and there would be one per connection, so that if someone
started to abuse their connection, only they would suffer. Once you get to a
service large enough to be worried about DoS attacks, you'd want this
architecture anyway because then you can distribute it out to multiple
machines. I was skeptical about how to go about implementing this sort of
proxy: how much CPU time do you give it? If it takes 1ms to deserialize a
message that then consumes 1s of server time, do you have to restrict it to
1/1000th the CPU time of the server? Note that other possibilities include
strict prioritization of the processes/threads (so the connections are
starved until the server becomes idle), and enforcing one-at-a-time
processing of messages.

His approach in web-amp was just to limit each serialized argument to 8kb.
The objection that this might not be enough is countered by the fact that if
you're sending more data than that, you should mark it explicitly (by
creating a publish/subscribe model), because there's a good chance that the
data is being used on the wrong side of the wire. The attacker is allowed to
do whatever evil they can accomplish in 8kb, maybe that means a 2k-deep
nested series of lists, but whatever it is won't be too big. I feel that at
some point you have to enforce a limit.. in web-amp, you must limit the total
number of arguments they can send you, or the number of method calls per
second, or something.

The non-DoS-related semantic typechecking (I'm expecting an int, is it really
an int?) is just as easily done with assert()s inside the method body. I want
this kind of checking to happen as close to the top of the method as
possible.. doing it in a RemoteInterface in some separate file feels wrong to
me. One approach is a func.guard method attribute (whose constructor takes
arguments much like the RemoteInterface methods do), which could be pulled up
to the top of the method body with a decorator. The big difference in thought
here is the idea of providing objects (which happen to implement a certain
set of methods) versus providing methods (which happen to be bound to a
particular object).

A lot of the typechecking concerns are eased with finer-grained capabilities.
Ideally, the worst they can do by sending you a weird object type is to cause
an exception. As long as you haven't registered an Unslicer that gives the
resulting object some ambient authority, you aren't going give them any new
privileges by invoking a method on something they *can* give you. Tyler says
you only do typechecking when you're considering granting them some new
privileges. The notion is that it's the bound-method capability that is the
basis of power, not what they do with it or what they send to it.

The constraints are useful for method documentation, especially if they can
be serialized and passed to an object browser, but can only document the list
of methods and the names/types of their arguments. The actual API description
still needs to be in epydoc, which can provide (non-machine-parseable)
argument name/type docs too.


positional parameters for interoperability with java:
-----------------------------------------------------

java doesn't have keyword args. To provide interoperability, the python-newpb
method call serializer needs to send args in strict order, the java newpb
receiver would ignore the argument names (only using the values). In the
other direction, the java method call serializer would send None for the
argument names, and the python receiver would use the local RemoteInterface
to turn the argument list into a kwargs dict.


Finally, I need to study the XML schemas in the web-calculus more closely. In
it, the bound method closure URL can be used for two purposes: a GET returns
the method schema (a description of what types the positional parameters will
accept), while a POST will invoke the closure. However, the object which
provided that URL has a class, and the method clause had a name, and the
method schema is always the same for any given (class, methodname) pair, so
even a fully send-time-checking implementation doesn't have to retrieve any
method schema more than once. I had first thought that there was some
reduncancy in the XML data being returned, but Tyler's put a lot of thought
and time into it to minimize the round-trips and avoid redundancy. newpb
would be well-served by studying his approach carefully.
