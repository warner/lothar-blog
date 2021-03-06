:title: mercurial
:date: 2007-07-09 21:29
:slug: 30-mercurial

Wow, so long since I updated this. Each time I remember that I **do** have
a technical blog, and think to add something to it, I am tempted to start by
rewriting the whole blog system in some brand new way that will make it
easier to post to (and, the theory goes, therefore make me more likely to
write in it). The process of writing more code creates something that I'm
even less likely to understand next time, and code begets more code. It's
like a depth-first search through an infinite design space. Bad idea.

And speaking of technical distractions, I've been playing with `Mercurial
<http://www.selenic.com/mercurial/wiki/>`__ recently. I like it. I moved
`Foolscap <http://foolscap.lothar.com>`__ from Darcs to Mercurial last week,
mostly to learn more about it, and I've been pleased. My main reason was to
make it easier for folks to hack on Foolscap: darcs is all fine if you're
running debian and someone else has compiled it for you, but if you have to
build it yourself you have to start by building GHC, which is a non-trivial
adventure.

Mercurial's plugin architecture is pretty nice: one line in the .hgrc file
tells it to import a .py file, which registers a set of new subcommands with
the main /usr/bin/hg entry point. Which reminds me that I want to adapt
Trac's plugin mechanism (which lets you drop an .egg file in a specific
directory and then reference modules inside it from the config file) to
Buildbot, to make it easier for users to get interesting code into their
master.cfg files. Not that huge of a change, but it would make the
installation instructions for that code to get simpler; no need to change
sys.path from within master.cfg .

And because the plugin approach makes it easy, people are writing fun
plugins. The Tk-based graphical revision browser is great (and has a little
tram-line-style graph of which revisions got merged into which, very cute).
The 'bisect' extension helps you do an efficient binary search for the
revision which introduced (or fixed) a bug.

I'm still trying to figure out the "forest" extension, though. I think it's
what I want for tracking a couple dozen separate small projects (things I've
been doing in CVS for years, since I can update just one at a time, or commit
the whole lot of them and push the work from my laptop to my desktop). But
for the life of me I can't figure out how to use it, and the documentation is
heavy on the per-subcommand reference and light on the big-picture
descriptions.

And mercurial is **fast**. The cgi-based web server lets them speed up the
initial checkout: for the full Foolscap repository, doing a 'darcs get'
through the naive (twisted.web) server took 22 seconds (of which probably 17
was network), whereas doing the equivalent 'hg clone' from a hgwebdir.cgi
server (under apache) took 6 total. Mercurial manages to store the history
more compactly too: the tree with full history under darcs was 4.4MB, and
2.9MB in hg.

I've been using Darcs for a year or two now, and we've been using it
extensively at `work <http://allmydata.org>`__, and it's fun (the incremental
commit feature is amazing, and I miss it in hg, and it wouldn't be impossible
to add). But every once in a while something explodes (possibly because we've
used 'darcs oblit' more than once, and that seems to be an underexplored
corner of the darcs jungle). I **really** like the append-only and
cryptographically-secure nature of hg revisions, and regret that you can't
securely and concisely name a specific darcs revision the way you can with
mercurial. Having spent a lot of time defining sha-256 hash-based identifiers
recently, I'm coming to be wary of any system that doesn't let me create
strong references like that.

So I'm looking forward to playing with it more. Commuting patches is nifty,
but for things like Buildbot and Foolscap I'm not really creating crazy
branches with patches that need to be held out of trunk for months at a time.
So I think hg has a lot of promise.
