:title: foolscap.lothar.com
:date: 2007-07-13 12:41
:category: twisted
:slug: 31-foolscap.lothar.com

I just finished building a Trac instance for Foolscap, now online at
http://foolscap.lothar.com/trac . It's got a (mercurial-based) code browser,
tickets, and a wiki.

Setting it up required some twisted.web hacking, because my setup puts a
twisted.web server out front, and reverse-proxies certain requests to a
separate Xen virtual machine which handles all CGI (for multiple sites, like
buildbot.net and foolscap.lothar.com). That CGI host is running apache, and
since URLs inside returned pages are not being rewritten, I had to use named
virtual hosts to distinguish between, say, http://buildbot.net/trac and
http://foolscap.lothar.com/trac .

But the normal twistd.web.proxy `ReverseProxyResource
<http://twistedmatrix.com/trac/browser/trunk/twisted/web/proxy.py#L158>`__
clobbers the Host: header when it forwards the request (setting it equal to
the new host being targeted). I suppose this is to hide the presence of the
proxy from the new host, but in my situation is has the effect of making it
impossible to use vhosts on the apache side to distinguish between requests
that were received for different hostnames.

So I subclassed and commented out that line, and apache is happy. Now that I
can have more than one trac instance on this box, I'm creating Tracs for
everything. Whee!
