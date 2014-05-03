
Primitives that could be useful in an Invitation protocol:

- basic unauthenticated DH
- PAKE2/PAKE2+
- SRP
- SAS
- SMP/OTR

Diffie-Hellman Key Agreement
----------------------------


PAKE2
-----

SRP
---
http://en.wikipedia.org/wiki/Secure_remote_password_protocol
http://srp.stanford.edu/doc.html

Setup: System has large prime N, generator g, k=H(N,g). Carol remembers
password P, Steve the Server knows a verifier Carol picks salt 's', computes
x=H(s,P), v=g^x, gives (s,v) to Steve. x is discarded.

Login: Carol picks random 'a', sends A=g^a. Steve picks random 'b' (secret),
computes B=k*v+g^b, u=H(A,B), S=(A*v^u)^b, K=H(S), sends B. Carol computes
u=H(A,B), S=(B-k*g^x)^(a+u*x), K=H(S), M1=H(H(N)xorH(g),H("carol"),s,A,B,K),
sends M1. Steve verifies M1, computes M2=H(A,M1,K), sends M2. Carol verifies
M2. S is shared session key, but docs say to use K for session traffic.

'B' needs to be equiprobable, I think that means DDH. 'u' must not be
revealed until after Steve has committed to 'A', but is then public. Carol
must show her M1 first, and Steve should not reveal M2 until M1 is verified.
Implementations must test A!=0, B!=0, u!=0, and the usual g/p checks.


SAS
---

SMP/OTR
-------

