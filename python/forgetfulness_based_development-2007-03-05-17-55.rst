:title: forgetfulness-based development
:date: 2007-03-05 17:55
:category: python

You're probably familiar with eXtreme Programming, and branch-based
development, and agile development. But I've discovered that I've been using
a new technique recently, that I call Forgetfulness-Based Development. The
way it works is this: I come up with something insanely complicated, that
takes me weeks to get my head around and document and implement and test, but
seems like it's the best way to solve whatever the current problem is. And
then I go away on vacation for two weeks, and forget absolutely everything
about it. And then I come back, and look at it again, and discover how little
I can understand. After a few days of cursing the fool who wrote the insane
thing, I start seeing ways that it could be done more simply, or more
generally, or more robustly, or more understandably. And then I write some
more code to replace the old stuff.

Lather, rinse, repeat, and eventually you wind up with a design that solves
the problem *and* makes sense to a new employee/developer. As the python
folks say, Readability Matters. And as Brian Kernighan says: "Debugging is
twice as hard as writing the code in the first place. Therefore, if you write
the code as cleverly as possible, you are, by definition, not smart enough to
debug it."

(of course, to make this work right, you have to take a lot of vacations. but
usually it's a sacrifice I'm willing to take.)

