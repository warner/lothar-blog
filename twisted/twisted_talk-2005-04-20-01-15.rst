:title: twisted talk
:date: 2005-04-20 01:15
:category: twisted
:slug: 4-twisted-talk

So I think the talk went really well. I spoke for about an hour before the
room was needed for another meeting, to about 10 or 15 OSAF developers. I
managed to cover the reactor, Protocols, Factories, building higher-level
protocols, Failures, Deferreds, reactor.run() vs twistd -y vs mktap/twistd
-f, and even a bit of twisted.web (the resource-tree model) and threads
(reactor.runInThread/runFromThread). The things that were on my list but
which I didn't get to cover were Cred, usage.Options, PB, and Interfaces.

But all in all I think the session helped a lot of people get their heads
around the architecture.. I think they're now in a position to understand the
existing HOWTOs and other documentation.

After the session, I sat down with Brian and two other OSAF folks: Lisa
Dusseault and Grant Baillie. They are working on WebDAV, and have a strong
interest in a functional WebDAV client library. As I understand it, this
library's top-level API would need to look like an abstract file system, with
directory lookups, pathnames, something like file handles, and file
attributes. Inside, it would need to have a back end which actually speaks
WebDAV to some server, creating new connections when necessary, or re-using
persistent connections is possible. There would also need to be some sort of
cache-management policy hting, since smart caching can make or break the
performance of a WebDAV session.

Given their needs, we agreed that a Twisted WebDAV client library would be a
great solution, and they've got the motivation and the knowledge (apparently
Lisa was one of the primary WebDAV folks at Microsoft) to pull it off.

I described the recent work that's gone into an abstract file system (by spiv
and others, for twisted.ftp), thinking that it would be the best place to
start. The next step will probably be to introduce them to spiv, and float a
post on twisted-python to see who else has an interest.

Brian also gave me a quick demo of Chandler, giving me a better idea about
where they're going and what their plans are. It's funny, about 15 years ago
I had a summer job at a research lab who had a similar goal. They were
working on OCR and search technology, and wanted to make a box that could
digitize and read all the random bits of paper that you produce in the course
of a day, then let you index the information contained on them in a useful
way. The Chandler folks want to take all the random bits of digital
information that you create in the course of a day (email, IMs, calendar
entries, todo lists) and organize/share them in a useful way. Kinda neat. I
look forward to seeing where it goes.
