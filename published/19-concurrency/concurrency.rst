:title: concurrency
:date: 2005-09-15 23:26
:category: twisted
:slug: 19-concurrency

Had a great chat with `Donovan <http://ulaluma.com/pyx/>`__ today, about
newpb and E and secure python and concurrency management. It turns out we
have some of the same ideas about interesting things to do with these kinds
of tools. He pointed me at `a language named Io
<http://www.iolanguage.com>`__ that's doing some neat stuff with lightweight
coroutines, and had some interesting thoughts on coroutines in python (making
protocol-parsing code look a good bit simpler than the purely data-driven
model that twisted Protocol classes tend to have).

