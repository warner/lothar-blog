:title: sparklines
:date: 2005-05-07 12:40
:slug: 8-sparklines

My friend Drew just sent this one along:

 http://bitworking.org/news/Sparklines_in_data_URIs_in_Python

I'm pondering things I might do with this. I've been using Data: URIs for one
of my projects, they're pretty handy and both Firefox and Safari are more
than happy to take ridiculously large ones (50k or more). Like Drew, I'm
wondering what I could do with sparklines.

The first thing that comes to mind is a compact representation of BuildBot
test results. When you look at the history of a single builder, a series of
builds over time, what you care about it how the results have changed from
one build to the next. I've been thinking about having the buildbot pay
attention to things like when any given test starts failing or starts passing
again, but until I get around to writing that code, you could use a sparkline
to represent the test results in a compact glyph, and then just show the last
50 of those. The user could then scan them visually to look for changes.

I'm not sure where else to use them yet. I'm tempted to write a Nevow
renderer to create them, though, because that would make it a lot easier to
insert them into other pages. That would let you use some HTML like: ``<div
nevow:render="sparkline" nevow:data="stuff" />`` and then implement a
`data_stuff` method that would return whatever you wanted to put into the
sparkline.
 
