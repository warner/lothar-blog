Slug: Git-over-Tahoe-LAFS
Date: 2017-02-02 16:24
Title: Git over Tahoe-LAFS

!BEGIN-SUMMARY!
Tahoe-LAFS provides reliability, integrity, and confidentiality, so you
can store important data safely across multiple servers. Git provides
version control and merge tools, enabling better coordination between
multiple authors. By using Tahoe as a Git backend, we can get both.
!END-SUMMARY!

## Motivations

### Dropbox-workalike

Tahoe's main API looks a lot like an FTP server: you can
add/replace/remove whole files, and manage directories. It has mutable
files, but it doesn't handle write contention very well, and small
changes aren't as efficient as we'd like.

It would be nice to use Tahoe as a replacement for Dropbox, but the
simple approach (each computer reading and writing to the same shared
directory) would have several problems:

* two sides modifying the same file at about the same time will probably
  result in one of the versions being lost
* two sides modifying the directory at the same time could clobber the
  directory entirely, depending upon the encoding settings and the
  number of simultaneous writes

One way to avoid simultaneous writes is to give each side exclusive
control over their own "publish" directory. All sides then watch the
publish directories from all the other sides, and merge their contents
into their local copy. Then, afterwards, they publish the merged
contents back out. With luck, this process will eventually converge, and
all sides will see the same thing.

### Private Git Server

Another use-case is to store Git repositories privately. Github offers
"private" repos, but in fact all the data in those repos is visible to
Github's servers. This enables a lot of valuable tooling, so it's a
reasonable tradeoff for many users. But if all you want is a secure
place to store a repository so multiple users can access it, and you
don't want the server to be able to read or modify the contents, then it
would be nice to use Tahoe as a Git backend.

This also dovetails with the Dropbox workflow, since we can use Git to
manage the merging between multiple publish-directories.

## Goals

So what we want is a
[Git remote helper](https://git-scm.com/docs/gitremote-helpers)
extension for Tahoe-LAFS. If we drop a program named ``git-remote-lafs``
on our ``$PATH``, then any ``git clone lafs:...`` will use our program
instead of the built-in HTTP/HTTPS/SSH functionality. Our program will
also be involved with any pushes and pulls to that remote.

The general idea will be to have each Git client have exclusive
ownership of a Tahoe directory. These clients will push to their own
directory, then pull from all the other clients' directories. A
higher-level tool will somehow subscribe to those directories so it
knows when to pull, and can use inotify (or equivalent) to watch a local
directory to know when to ``git commit`` and ``git push``.

## Git Objects

Time for a quick refresher about Git's
[object model](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects):

* each Git repo is an object store, mapping SHA1 to a typed chunk of data
* files are stored as "blob" objects
* directories are stored as "tree" objects, which just map child name to
  an object-id (either a blob or another tree), plus a file mode
* "commit" objects reference parent commits, comments, and a tree object
* the Git repo also remembers "refs", which map branch/tag names to a
  commit object
* Git can store all of these objects "loose", one local file per object,
  in ``.git/objects/XX/XYZZ``
* or, it can "pack" many objects into a single file, in
  ``..git/objects/pack``, with zlib compression, inter-object deltas,
  and an index for fast access

When you run ``git push``, git runs a clever protocol that attempts to
minimize the amount of data it has to transfer. First, it figures out
what refs the remote end currently has. Then it runs a
graph-reachability algorithm against the local tree, to make a list of
all objects that are reachable by the references being pushed, but not
reachable from the remote's current refs. (link to git command to build
this list). This it builds a single packfile with all of these objects,
expressed as deltas against objects it knows the remote end has access
to. Then it merely sends this packfile over the wire.

The remote end drops the packfile into the local object store, then
verifies that it can find all the new refs it's been sent (and every
object they can reach). The routine that reads objects from
``.git/objects/`` (using packfiles if necessary) takes care of the rest.

A similar routine happens when ``git fetch`` pulls objects from a remote
repo.

Git remote helpers can do whatever they want, as long as the right
objects wind up in the right place.

## Efficiency

The simplest approach would be to store each Git object in a separate
Tahoe immutable file, and the refs in separate mutable files. This is
inefficient in a lot of ways.

First, let's distinguish between the different kinds of objects we're
dealing with:

* "source files": the files from the original workspace, which you
  manipulate with your editor or other application, and add with ``git
  add``
* "git objects": the blobs and trees and commits that git knows about
* "tahoe objects": CHK (immutable) and SSK (mutable) tahoe files and
  directories

Now, in the one-Tahoe-object-per-Git-object scheme:

* each tahoe object is the size of the latest version of that source
  file, so making a 1-byte change to a 1MB file causes the Tahoe
  filespace to grow by a whole megabyte each time
* "subscribers" (Git clients that do ``git pull`` on a regular basis)
  have to download that whole megabyte too
* new clones must download a megabyte for each historical version  

Clearly we have a large design space for this extension. There are
several things we might try to optimize:

* data pushed into Tahoe for each change
* number of objects added to Tahoe for each change
* rate of Tahoe garbage (dereferenced tahoe objects) generated per
  change
* amount of overhead (garbage-collection) done during push
* number of objects fetched by subscribers for each change
* amount of data fetched by subscribers
* number of objects / amount of data fetched by new clones who care
  about getting the whole history
* same, for new shallow clones (those who don't care about history)

## Necessary Deltas

For the Dropbox use-case, we only need to retain history as far back as
the oldest client. Once all clients have caught up, we don't need to
keep the history any more (unless we're specifically trying to provide
revision control, as opposed to merely keeping directories in sync). The
most likely case is that we'll have some number of "live" clients, who
are generally up-to-date, and some number of "stale" clients (e.g.
laptops that haven't been plugged in for a while) which only get updated
rarely. And then occasionally we'll add a new client, who needs to be
brought up-to-date from nothing.

If you think about a linear history, we might have one "stale" client at
version 5, another stale client stuck at version 8, and then all the
"live" clients are at version 20. One of the live clients makes a change
(bringing us to 21), then the other live clients catch up. In that case,
we need to be able to bring a new client from "0" directly to 21, and we
also need enough information to get from 5->8 and from 8->21.

I'm diving into this now, because it will inform our choices about data
representation later.

## One-packfile-per-push

The next-most-efficient scheme would be to write out one Git packfile
for each push. Basically each time our helper is told to push something,
it should build a packfile that contains every object that isn't already
in the remote, which means each object that we don't remember pushing
before. This packfile can use the previous value of the ref as a basis
(storing deltas against those objects instead of complete copies, when
that helps).

* we push one object per change (the packfile), plus changing the
  mutable ref
* this object is as small as it can be, at least considered in
  isolation. The new data in the packfile could be smaller if it were
  zlib-compressed against other objects, e.g. if the packfile were
  merged with other packfiles. However that would increase the amount of
  data the subscriber would have to fetch.
* subscribers only have to read one packfile, so their workload is
  nearly minimal
* new clones have to read all the packfiles, which loses out on the
  compression opportunities we could get if we could merge the packfiles
  all together

## One-packfile-per-client-delta

The most efficient thing possible for full-history downloaders
(subscribers and new clones) would be to have one packfile per old
client version. In our example with clients at versions 5, 8, and 21, we
would need a "0->21" packfile (for new clones), a "5->21" packfile (in
case that version-5 client wakes up and needs to update), and an "8->21"
packfile (for the version-8 client). That doesn't minimize the
tahoe-side *storage* (since we're storing multiple copies of the same
data), but it does minimize the work that downloaders have to do.

For shallow-history downloaders, we don't need the whole "0->21"
packfile, we just need a "21" packfile (one which contains the current
tree, but none of the history). So we'd need "5->21", "8->21", and "21".

But again, we're storing three copies of the latest tree, just to allow
that version-5 client to only fetch one tahoe object. And we aren't even
convinced that this stale client is going to show up any time soon. So
we can compromise by storing a "5->8" packfile, and an "8->21" packfile.
If we're supporting full-history clones, we'll also store a "0->5"
packfile, and new clones will need to grab three tahoe objects. If not,
we'll store a "21" packfile, and new clones only grab one.

The general approach will be for each new push to add a new packfile
(e.g. 21->22, then 22->23, etc). Live subscribers will need to fetch
each packfile anyways, to catch up quickly, so having them around is
efficient. But eventually the number of these small (one-change)
packfiles will grow uncomfortable, and the work needed for new clones
will grow (linearly with the number of changes). So every once in a
while, we'll want to "consolidate", replacing all the one-change
packfiles with a single many-change packfile. If there are any stale
clients, this packfile should go from the least-stale client's
last-known version, to the current version. If there are no stale
clients, it should just contain the entire history (0->current).

This incurs a certain amount of overhead for the periodic consolidation,
causing ``git push`` to take longer than usual, and creating tahoe-side
garbage (as the old small-packfiles are removed from the tahoe
directory).
