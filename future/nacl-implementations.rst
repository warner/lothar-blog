===========================
NACL Implementation Roundup
===========================

C (with low-level speedups)
---------------------------

* Canonical NaCl library (http://nacl.cr.yp.to/install.html)
** Current Version 2011-02-21: http://hyperelliptic.org/nacl/nacl-20110221.tar.bz2
** C, C++
** does *not* have Ed25519 yet

* SUPERCOP (http://bench.cr.yp.to/supercop.html)
** Current Version 2012-09-28: http://hyperelliptic.org/ebats/supercop-20120928.tar.bz2
** includes Ed25519
** organized for benchmarking, not so much for real use

* https://github.com/agl/curve25519-donna.git
** just curve25519
** portable and optimized
** incorporated into canonical NaCL

Bindings (for other languages to wrap a C implementation)
---------------------------------------------------------

* https://github.com/seanlynch/pynacl
** Python, does not include Ed25519
** various branches for various build options, both ref and optimized

* https://github.com/warner/python-ed25519
** Python, only Ed25519
** uses 'ref' version


Pure Python
-----------

* "ed25519.py" in http://ed25519.cr.yp.to/software.html
** demonstration code, remarkably slow

* https://bitbucket.org/dholth/ed25519ll
** (also has a C binding, using 'ref10' version)

pure-python:
crypto_sign_keypair_fromseed: 4.83ms
crypto_sign: 10.01ms
crypto_sign_open: 19.45ms

* Matthew Dempsky's pure-python sample code
** http://cr.yp.to/papers.html#naclcrypto , pages 6+7
** "slownacl" directory of https://github.com/mdempsky/dnscurve
** dempsky-curve25519.py
** crypto_scalarmult_curve25519_base takes 5.6ms on my laptop

(1000 byte messages where applicable)
crypto_scalarmult_curve25519: 5.80ms
crypto_scalarmult_curve25519_base: 5.60ms
crypto_stream: 4.34ms
crypto_stream_xor: 4.85ms
crypto_auth: 139.51us
crypto_auth_verify: 152.95us
crypto_onetimeauth: 473.58us
crypto_onetimeauth_verify: 478.95us
crypto_secretbox: 5.50ms
crypto_secretbox_open: 6.11ms
crypto_box_keypair: 9.72ms
crypto_box: 11.60ms
crypto_box_open: 12.13ms
crypto_box_beforenm: 6.02ms
crypto_box_afternm: 5.56ms
crypto_box_open_afternm: 6.07ms



Javascript
----------

* http://flownet.com/ron/code/
** curve25519 and ed25519
** http://flownet.com/ron/code/djbec.js
*** Uses jsbn and jsSHA
** http://flownet.com/ron/code/fast-djbec.js
*** jsbn, jsSHA, and Michele Bini's curve25519 code
