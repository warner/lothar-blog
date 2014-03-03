:title: Levenshtein Distance
:date: 2008-04-28 18:45
:slug: 34-Levenshtein-Distance

A library just showed up in debian ("python-levenshtein") to measure the
`Levenshtein Distance <http://en.wikipedia.org/wiki/Levenshtein_Distance>`_
between two strings: the minimum number of edits (inserts, changes, deletes)
necessary to turn one string into another.

I've been thinking about ways to implement efficiently-edited large mutable
files for `Tahoe <https://tahoe-lafs.org>`_, and it seems like a tool
like this might help. Something clever like what rsync does is probably going
to be involved too. The trick is that you want to determine what deltas to
store without reading the whole file over the wire, from a server who isn't
allowed to see the plaintext. You can store whatever ciphertext hashes you
want on the far end. We're planning to provide insert/delete delta messages
in the server side, using something like Mercurial's "revlog" format. The
question is how to efficiently figure out the deltas on a very large file.
