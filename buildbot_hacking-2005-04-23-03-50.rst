:title: buildbot hacking
:date: 2005-04-23 03:50
:category: 

I'm pushing to get a new `BuildBot <http://buildbot.sf.net>`__ release out on
monday, so the last few days have been a flurry of commits (and the weekend
will probably be the same). I was very pleased to hear that the Boost crew
have implemented a `Buildbot <http://build.redshift-software.com:9990>`__ to
run their (very large) regression test suite, especially because Dave Abrahms
and I talked about setting one up two years ago, at PyCon, and I was never
able to give them the time to make it happen. I was even more pleased to hear
that their goal is to move all their testing over to buildbot. You couldn't
ask for better marketing than for the STL heir-apparent to be using your
project :).

Both Thomas (at `Fluendo <http://build.fluendo.com:8080/>`__) and the Boost
folks have patched their buildbots to allow the waterfall display be themed
with CSS, and the results look great. I'm looking forward to getting Thomas's
code pulled into the mainline sources.. finally a way to make the waterfall
display less ugly.

Finally, the metabuildbot is shaping up. This is a buildbot that works to run
the buildbot's own unit tests. I need to find a reasonable hostname and link
for it, then I'll make it publically visible. Bear has put a lot of time so
far into making the win32 slave work correctly, with no success yet (the
specific problem is that I'm using Arch to get up-to-date sources out to the
buildslaves, and tla is not happy on win32, some kind of 260-character limit
on pathnames that tla runs up against when it does a checkout). I've dropped
back to CVS for now (with a three-hour timeout in the hopes of getting around
sf.net's enormous anoncvs latency), but a separate bug in the buildslave,
compounded by a bug in the buildslave's error-handling code, have conspired
to get the win32 slave into a state that requires manual intervention to
un-jam. Grr, stupid windows.
