:title: urllib3
:date: 2012-06-25 04:42
:category: python
:slug: 47-urllib3

Today I learned about the `urllib3 <http://pypi.python.org/pypi/urllib3>`__
module. The biggest feature (from my point of view) is that this one can
properly validate SSL sessions.
!END-SUMMARY!
The python 2.x ``urllib``, ``urllib2``, and
``httplib`` libraries all vaguely speak SSL, but none of them actually look
at the certificate they receive (and will cheerfully silently connect to a
man-in-the-middle). This mode only provides protection against passive
eavesdroppers. Until recently it wasn't even obvious that the stdlib modules
had this problem (so a lot of folks writing HTTPS clients have not been
getting the protections they imagined they would get), but at least the py2.7
docs include a big red warning.

It's not a trivial thing to fix (at least without changing the API), but the
temptation to do just that is indicative of a deeper issue in security
engineering. As a consumer of the urllib API, you want your job to end when
you provide the URL: you expect it will be "secure" by default. But you've
provided a (domain) name that isn't "Secure" in the sense of `Zooko's
Triangle <http://en.wikipedia.org/wiki/Zooko%27s_triangle>`__, so there is
some other party who has the right to change what your reference points to.
The traditional web/SSL approach is to start by letting DNS tell you which IP
address to aim your packets at, then let the internet's routing layers
deliver your packets to *somebody*, then set up an SSL connection with that
somebody, then accept the connection if the somebody's SSL certificate was
signed by one of the CA roots that you trust. Ultimately your configured CA
roots get to choose who you connect to. We're content with making the DNS
layer implicit (using a pre-configured list of a.gtld-servers.net addresses
and their responses), as well as the routing layer (leaving that up to your
ISP), but a library author isn't quite so comfortable making assumptions
about which CA roots you'd like to use. Web browsers, which are making
decisions like this for their users all the time, come with a slowly-changing
list of CAs which get reviewed frequently. Embedding a list into a static
library is probably more power than the authors really wanted to claim.

So with ``urllib3``, you must give it a list of CA roots (and pass
``cert_reqs="CERT_REQUIRED"``), and then it only connects if the site's cert
is signed by one of those CAs. If you know which CA a given site uses, you
can achieve a limited form of cert-pinning by only including that one CA root
in the list you give it. That reduces the set of people who can control your
connection to just the one CA. It looks like the companion `requests
<http://pypi.python.org/pypi/requests>`__ library has facilities to grab the
CA list from your OS if it provides one, which makes it easy delegate the
decision to your OS vendor.

``urllib3`` also provides connection pooling: keeping an HTTP(S) connection
open for multiple requests, which is a big win for performance, especially
when doing a lot of little requests.

It looks like Python3 fixes this too, with a stdlib ``urllib.request`` module
that takes a CA list just like ``urllib3``.
