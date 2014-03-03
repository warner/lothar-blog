:title: hacking
:date: 2005-07-13 23:08
:slug: 17-hacking

The last few weeks have been mostly filled with `hacking
<http://buildbot.sf.net/>`__ hacking. I'm neck-deep in the implementation
phase of a big new set of features, and it's taking *forever*. But I think
I'm finally past the hardest part, the design issues that remain to be solved
are at last medium-sized ones instead of huge ones, and even the unit tests
pass. So I'm feeling pretty good about that.

I'm also trying to hack on `Petmail <http://petmail.lothar.com/>`__ a little
bit more. There's a spam conference at Stanford next week that I'll be
attending, and even though it's unlikely I'll be showing it off to anyone,
I'd like to be sufficiently back in the Petmail mindset that I can discuss it
intelligently while I'm there.

I'm trying to shift Petmail's configuration interface from the current Gtk
app into a web page one, using `Nevow <http://nevow.org/>`__, because
eventually (when Bill gets some time to work on the Thunderbird plugin) the
send/receive mail interface will be through XMLRPC (or whatever Mozilla code
can get to most conveniently). I haven't figured it out yet, though, nevow
provides some nice features for free, but I don't yet know if they're the
ones that I need to implement this sort of add/edit/remove configuration
stuff.

Also, I'm moving Petmail development over to `Darcs
<http://abridgegame.org/darcs/>`__. I've been a bit frustrated with my recent
Buildbot development push, because I'm using Bazaar on my laptop, with a
local repository so I can make commits offline, but pushing changes back and
forth between repositories is enough of a hassle that I just don't do it. So
I'm doing all the buildbot work slouched over my laptop (which I really like,
but the keyboard is making my hands just a little bit uncomfortable), rather
than the desktop with the proper keyboard and proper chair. It looks like
Darcs would make it a bit easier to fling changes from one place to another,
so using it might encourage me to do development anywhere I feel like. (plus,
I should really get a new monitor for the desktop machine.. my
ex-brother-in-law has a gorgeous 20" LCD, something from Dell, which I'm
really tempted to splurge for).

So anyway, there's a Darcs tree for Petmail available at
http://petmail.lothar.com/repos/trunk , which replaces the old CVS repository
on that same site. I don't have a Darcs equivalent for ViewCVS up yet,
though. I've seen a web-based Darcs patch viewer, but I wasn't really
impressed. So I'll keep looking.
