:title: OSAF Twisted talk
:date: 2005-04-19 02:44
:category: twisted
:slug: 3-OSAF-Twisted-talk

This is a rough outline of the talk I'll be giving at the OSAF tomorrow.

::

 definition of Twisted, resources:
  http://www.twistedmatrix.com
   svn://svn.twistedmatrix.com/svn/Twisted/trunk
   http://twistedmatrix.com/cgi-bin/mailman/listinfo/twisted-python
   http://twistedmatrix.com/bugs/
   http://twistedmatrix.com/buildbot/
  #twisted, #twisted.web on freenode
 
 relationship of subprojects, dependencies:
  core, names, mail, web, words, conch, trial
  zope.interface, python2.2
  optional: pyopenssl, db stuff
 
 directory overview:
  twisted.python: usage.Options, Failure, log
  twisted.internet: reactors, base classes for Protocol+Factory, Deferred
  twisted.protocols: simple protocols: finger, socks, telnet
  subproject directories
  doc/*/howto
  doc/core/howto/tutorial/listings/finter/*.py
 
 motivation:
  simple client
  simple server
  not-so-simple server
  client+server
  need for a generalized solution
  threads, processes, event loop
 event loop:
  asyncore
  reactor
 
 picture: reactor with select() call, sockets in .readers/.writers
  sockets have .doRead, .doWrite, are scheduled with .addReader/etc
  timers
  different kinds of reactors, using other event loops: gtk, kqueue
 
 picture: Protocol with Transports, reactor
  Protocol: connectionMade, dataReceived, connectionLost, transport.write
 
 how do those Protocols get created?
 reactor.listenTCP(port, factory)
 picture (server): Protocols, Factory
  listening socket (Port) points to Factory, creates new Protocols
  Factory gets startFactory, stopFactory, buildProtocol
  Protocols generally have .factory
 
 reactor.connectTCP(host, port, factory)
 picture (client):
  Factory gets startedConnecting, clientConnectionFailed, clientConnectionLost
   as well as startFactory, stopFactory, buildProtocol
  Connector is responsible for getting a connection to host+port+factory
   possibly multiple times, for ReconnectingClientFactory
  skip over Connector stuff
 
 writing Protocols, using existing ones
 picture: t.p.finger.Finger
  overridable methods for getUser, getDomain, forwardQuery
  subclass, override method
  make a Factory which instantiates your new subclass
  attach to listenTCP
 
 Protocols are used for both clients and servers
  state machine
  return one-shot results with Deferreds
  return multi-shot results by overriding methods
 
 larger protocols have more complex setup
 
 names: protocol parses the query, hands to factory
  factory does self.handleQuery, asks self.resolver, calls self.sendReply
  # good example of API, use of deferred: t.n.server.py:120, dns.py:1050
 
 web: basic HTTP protocol creates Requests, then does req.process
  twisted.web.site implements a Resource tree
   picture(web): root, getChild(), isLeaf, render(req)
   specialized subclasses provide CGI processing, static.File, distrib
 
 imap: involves cred, Mailbox objects, Message objects
 
 top-level invocation:
  __main__, reactor.run()
   connectTCP, listenTCP
  or, creating an Application, then using twistd
   motivation: daemonization, logging, setuid/chroot, reactor, profiling
    think /etc/init.d
   picture: trees of Service/MultiService objects
    each gets startService, stopService
    t.a.internet.TCPServer(port, factory), TCPClient
   twistd -y foo.tac, script which creates an Application object
    sidebar: python as a configuration language
   serialize the Application, then launch it again later: twistd -f foo.tap
   shortcuts for common applications: mktap
   mktap plugins: Options, makeService(), register with plugins.tml
 
 threads:
  nothing here needs threads
  where are they useful?
   wrapping blocking APIs: adbapi in particular
   integrating with other code
  threadpool: run a function in a thread, tell me when it is done
 
 t.p.log:
  log.msg(msg, msg) emits a log
  log.err() emits the current exception
  log.err(f) emits a Failure object
  log output goes to an observer
  running from twistd: goes to twistd.log, or syslog
  running from __main__: log messages are discarded
  log.startLogging()
 
 Failure:
  encapsulates a python exception
  can be serialized, printed, queried about what caused it
  Failure() inside an except: block wraps the current exception
 
 Deferred:
  callback management
  use web.client.getPage as an example
  synchronous style:
    a=foo()
    b=bar(a)
    baz(b)
  asynchronous style:
    d=foo();
    d.addCallback(bar)
    d.addCallback(baz)
  callback vs errback, ladder diagram
  fire-before-addCallback is safe
  callbacks can return Deferreds: sub-ladders
 
 usage.Options:
  create subclass, attributes indicate valid options
   optFlags, optParameters, subCommands
   define opt_foo(self,str) to implement --foo=str
  methods can customize processing further
   parseArgs, postOptions
  str() provides usage message
  Options implements the dict interface, opts['foo'], opts['v']
  usually invoked with opts.parseOptions(), which grabs sys.argv
  why? mktap plugins use the 'Options' class from the plugin to parse argv
 
 lore:
  turn .xhtml into .html (or .latex, others)
   inline listings, pretty-print python code
   links to epydoc-generated API docs
 
 pb:
  translucent RPC
  f=pb.PBServerFactory(root); reactor.listenTCP(port, f)
  cf=pb.PBClientFactory(); reactor.connectTCP(host, port, cf)
  d=cf.getRootObject(); d.addCallback(dostuff)
  ref.callRemote("method", args)
  def remote_method(self, args)
 
 cred: howto is really good
  avatar, portal, realm, credentials, checker, mind
  portal has a set of checkers
  checker gets credentials, decides if they're ok, provides an avatarID
  realm gets avatarID and desired interfaces, returns an avatar
  protocol gets back the avatar, does stuff with it
 
 interfaces: PEP245-style
  twisted/python/components.py
  zope.interface, tiny portion of Zope3
  many APIs want "object that can be adapted to IFoo" rather than an instance
   of a specific class
  some systems use it extensively: nevow's 'context': IRequest,ISession,ISite
