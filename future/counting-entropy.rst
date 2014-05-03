


Entropy Counters
================

Kernel RNG subsystems try to estimate how much entropy they contain. This can
be a pretty fuzzy concept, and invokes things like "information-theoretic
security" and attackers with infinite computational power. The intentions are
good, but ultimately aren't as useful as you'd like.

It really only makes sense to measure entropy when it's coming from a source
that is designed to be measured. Entropy is a property of a *process*. If I
roll an 8-sided dice for a while, and convince myself that it produces evenly
distributed numbers, then it's fair to say that each new roll produces three
bits of entropy. If I roll it four times and write the results into my
/dev/random, I should feel justified in raising the kernel's entropy counter
by 12 bits.

keyboard inputs: not so random

goals of counting entropy:

* initial blocking: don't allow bad usage until pool is safe to use
* different usage of /dev/random and /dev/urandom: protecting some uses
  against the omnipotent attacker
