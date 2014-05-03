Ladders of Power
================

I visualize the "login" process a climbing a ladder. Higher rungs represent
more power, and you get there by revealing a secret, or by some other object
(server) deciding to grant you access. You can voluntarily drop to a lower
rung by forgetting something, or you might be forced down when some other
object decides to revoke your access.

Hashing a password to derive some token (then forgetting the original) is
another way to drop down a rung. An attacker who gets the hash can then do a
dictionary attack to climb back up to the level of the original password, and
the step is harder if the hash involves some stretching.
