How To Trust Your Software
==========================

Each day, we use software written by thousands of different developers,
probably closer to hundreds of thousands. Getting these words to the blog
server relies upon text editors, windowing systems, OS kernels, network
stacks, web browsers (with hundreds of libraries for graphics, protocols,
language runtimes, unicode handling, etc), server-side components, and
databases, all doing mostly the right thing.. Just using an alarm clock to
wake up this morning depended upon a few hundred lines of code in its
embedded micro-controller.

We rely upon this nightmare of moving pieces because we have no other choice.
But we still draw a distinction between code that we're willing to trust,
code that we'll run but not depend upon, and code that we aren't even willing
to execute. How do we decide which bits of code are worthy of trust?

This ties closely into the discussion about cryptography in JavaScript. One
aspect (but not the only one!) is getting JS from a server which then
encrypts some data. Is it any better to do this (hoping that the JS they gave
you will hide your plaintext from the server) than to just give the plaintext
to the server (hoping that they'll encrypt it before storing it, etc)?

Similarly, iPhone apps are signed by their developer, with keys blessed by
Apple...

Trust in software derives from being able to predict its actions, whether by
studying the code, or observing what happens when you run it. You can
delegate this analysis to others: non-programmers

I think there's a spectrum here:

* hardware, ROM
* upgradeable firmware
* installed applications
* ephemeral web pages, server behavior

My alarm clock is twenty years old, and is probably run by a single MSI chip
with a few hundred gates: just barely smart enough to count to 12:00 and then
start over again. If someone wanted to trick me into waking up an hour late
and missing that important meeting, they'd have needed to begin their
nefarious plot back in 1992, predict when this important meeting was going to
happen, build a substitute chip (which would cost more without efficiencies
of scale), insert it into a specific box, then arrange for me to buy that one
box instead of an undoctored one, then wait patiently for a few decades.

If that same attacker wanted to trick me into thinking that Slashdot was
espousing.. I don't know, something that Slashdot wouldn't normally espouse,
they could get control of the network (compromise one of the routers between
here and there, DNS-poison my box into sending traffic to them, or compromise
Slashdot itself), then wait for my IP address to send a request, and quietly
replace that one response with the doctored version. When I tell my friends
about it, they don't believe me because they only get the undoctored original
page. And when I go back to fetch it a second time, I also get the original,
making me wonder if maybe I just imagined it.
