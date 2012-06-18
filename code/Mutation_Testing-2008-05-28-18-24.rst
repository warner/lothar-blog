:title: Mutation Testing
:date: 2008-05-28 18:24
:category: code

I've often thought that it would be a great idea to test your test suite by
randomly changing bits of code and seeing if the tests catch it. It turns out
that other people feel the same way: I just saw a Ruby library named "Heckle"
show up in debian sid (the package is named libheckle-ruby). The blurb says:

  Heckle is a mutation tester. It modifies your code and runs your tests to
  make sure they fail. The idea is that if code can be changed and your tests
  don't notice, either that code isn't being covered or it doesn't do
  anything.

In a security context, this is similar to an approach thought up by (I
believe) David Wagner, Ka-Ping Yee, and Mark Miller, during the security
analysis of Ping's electronic voting software. The unusual challenge was that
the defined security goal was to be safe against the author of the software,
not just the usual malicious attackers (who try to provide bad input, or make
the code act in surprising ways). Their scheme was to have one team modify
the code to insert intentional errors (or opportunities for mischief), then
the second team try to find those errors. If the second team finds other
errors, then the code is obviously buggy, and loses. If the second team can't
find the errors, then the code is too complicated to analyze, and it loses.
If the design of the code is so straightforward that bugs and backdoors stand
out like a sore thumb, the code wins.

Of course, this requires really good, really tightly specified unit tests. In
my experience, if you're using the right language, a test that specifies the
desired result so precisely is effectively your functional code anyways, so
you have to be careful to define your tests in some way that doesn't mean
you're writing the same code twice.

I don't know Ruby, but I may need to learn enough about it to be able to read
this Heckle library and see if it can be ported to Python.
