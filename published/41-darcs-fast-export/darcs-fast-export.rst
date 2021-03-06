:title: darcs-fast-export
:date: 2009-06-24 12:03
:category: version-control
:slug: 41-darcs-fast-export

So idnar just turned me on to `darcs-fast-export
<http://vmiklos.hu/project/darcs-fast-export/>`__, which can be used with
git-fast-import to quickly convert a repository from darcs to git. I've been
using Git more and more in the last few months, and I'm growing quite fond of
it. Tahoe is managed in darcs, and I've been using a private Git mirror to
manage the several dozen feature branches that I work on at any given moment.
I wanted to make a more-official mirror that would be reasonable to publish
on `GitHub <http://github.com/>`__.

I had to patch the darcs-fast-export script a little bit, one because our
darcs repository happens to have some bad (non-UTF8) characters in some old
patches (before darcs started rejecting those), and two because I wanted to
preserve our tag names (like "allmydata-tahoe-1.4.1", and darcs-fast-export
was squashing the hyphens down to underscores).

Tahoe has about 4000 patches. darcs-fast-export started doing about
170ms/patch (20 patches per second), and towards the end of the job is
slowing to about 1.1s/patch. In contrast, when I first tried the conversion
with tailor, the "darcs pull" operation was taking about 20 seconds per
patch. Tailor finished after 13.5 hours. darcs-fast-export took 42 minutes.

darcs-fast-export also takes care of incremental updates, so I can update the
mirror later as more darcs patches arrive. It also suggests that it can be
used bidirectionally. I might start using this to move my git patches back
into trunk.
