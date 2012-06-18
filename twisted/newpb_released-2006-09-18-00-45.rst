:title: newpb-0.0.2 released
:date: 2006-09-18 00:45
:category: twisted

I finally got some twisted time this weekend, so I fixed ticket <a
href="http://twistedmatrix.com/trac/ticket/1999">#1999</a> and moved newpb
out of the Twisted subdirectory entirely, renaming it to <a
href="http://twistedmatrix.com/trac/wiki/FoolsCap">Foolscap</a> in the
process. I also released version <a
href="http://twistedmatrix.com/~warner/Foolscap/foolscap-0.0.2.tar.gz"
>0.0.2</a>, so there's a complete tarball ready to install and play with.

Having it live outside the Twisted tree has a number of advantages. Twisted
is mature enough to have moved to a slower development model that preserves
stability at the expense of making new development easy. Each potential
change to the codebase must be reviewed before being applied to the trunk, so
all development takes place on branches and must serve to fix a specific
ticket. Very little of the newpb development falls under this model, and
there are a distinct scarcity of people able to review newpb code. By moving
it outside the Twisted tree, I can continue to work on it in a more suitable
development model.

In addition, moving it outside the <tt>twisted.</tt> package makes it
<b>much</b> easier to test and deploy. When it lived in
<tt>twisted/pb/*.py</tt>, you had to actually install it before using it,
into the same directory as the rest of Twisted. Now that it lives in
<tt>foolscap/*.py</tt> instead, you can run it from the source tree. This
will make things easier for everybody.

The new name is a bit of a compromise, though. I'm not entirely satisfied
with "Foolscap". It has some good properties (google thinks it is fairly
unique, it has "cap" which might make you think of capabilities, it has "oo"
which might make you think of objects, there's the visual of a twisted
foolscap of paper, the jester's hat-and-bells could make a nice logo). But it
also has some bad ones (MarkM points out that there's enough negative baggage
around the word "capabilities" that you might not want "cap" in your protocol
name, using the word "fool" gives some negative connotations, the
promise-pipelining aspects are really more interesting than the capabilities
ones, and anyways "foolscap" doesn't really flow off the tongue in a glib
manner). But it needed a name to live outside Twisted, and now it has one.
That might change, but Foolscap should get us through the next couple of
months.

I've been staring at E's CapTP protocol a lot, thanks to help from Mark
Miller, trying to understand what their goals are, how they accomplish them,
and what pieces would be useful to implement in Foolscap. What I learned last
week was how the CapTP 3-Vat introduction system works. I think I can
implement it in Foolscap, but I'm trying to decide if it's worth it. CapTP
does some funny tricks to make sure that messages which introduce two Vats
are delivered in the correct order relative to other messages between those
Vats (this is called E-Order in MarkM's papers). I assume this is a good
property to maintain (my general approach is to assume that everything MarkM
does has a good reason behind it, and that if I work at it long enough I may
learn that reason for myself, but for now just shut up and implement it).

But a lot of CapTP is tied up in Promises, and I'm still getting my head
around how to provide something in python that resembles a Promise and is
still useable. We don't have a lot of the language features that E does, in
particular the way that an E object holding a reference to a Promise will
eventually discover (after the promise has been resolved) that they're
holding a reference to some other object. We don't have that sort of silent
slot mutation in Python, so I'm trying to figure out what would be a
meaningful equivalent. So far the Promise syntax is looking something like::

 p2 = send(p1).foo(args)
 #  equivalent of E's:  p2 = p1 <- foo(args)

Of course you can also use <tt>send()</tt> on non-promises if you just want
to do an eventual-send. This is a more precise way to accomplish what I've
been (crudely) doing with <tt>reactor.callLater(0,..)</tt> all these years.
I'm also writing a <tt>sendOnly</tt> for when you want to throw away the
return value. E has compiler support for this, it knows whether the results
of the <tt>send</tt> are used or not, and can switch between <tt>send</tt>
and <tt>sendOnly</tt> automatically. Python does not have such a context
sensor, so we have to do it by hand.

Then, when you want to interface back to the synchronous world, you use
<tt>when()</tt> to turn the promise into a Deferred, to which you can then
attach some code to run::

 def _stuff(value):
     print value
 d = when(p2)
 d.addCallback(_stuff)

Trying to get this to work with the actual eventual-send queue and make the
result Promises work correctly is making my head spin. I need to sit down
with Zooko on this stuff, he'll understand it well enough to help me get my
brain around it.
