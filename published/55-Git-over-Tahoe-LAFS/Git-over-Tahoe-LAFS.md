Slug: 55-Git-over-Tahoe-LAFS
Date: 2017-02-07 01:17
Title: Git over Tahoe-LAFS
Category: tahoe

!BEGIN-SUMMARY!
Tahoe-LAFS provides reliability, integrity, and confidentiality, so you
can store important data safely across multiple servers. Git provides
version control and merge tools, enabling better coordination between
multiple authors. By using Tahoe as a Git backend, we could get both.
!END-SUMMARY!

## Motivations

### Dropbox-workalike

Tahoe's main API looks a lot like an FTP server: you can
add/replace/remove whole files, and manage directories. It has mutable
files, but it doesn't handle write contention very well, and small
changes aren't as efficient as we'd like.

It would be nice to use Tahoe as a replacement for Dropbox: sharing a
directory among multiple computers, generally all owned by the same
person. But the simple approach (each computer reading and writing to
the same shared directory) would have several problems:

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
all sides will see the same thing. By recording some amount of history,
we can provide the merge process with more context to work with.

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
extension for Tahoe-LAFS. In case you aren't familiar with them,
remote-helpers let you drop a program named ``git-remote-lafs`` on our
``$PATH``, and then any ``git clone lafs:...`` will use our program
instead of the built-in HTTP/HTTPS/SSH functionality. Our helper will
also be involved with any subsequent pushes and pulls to that remote.

The general idea is that each Git client gets exclusive ownership of a
single Tahoe directory. These clients will push to their own directory,
then pull from all the other clients' directories. A higher-level tool
will somehow subscribe to those directories so it knows when to pull,
and can use inotify (or equivalent) to watch a local directory to know
when to ``git commit`` and ``git push``.

## Git Objects, Git Push

Time for a quick refresher about Git's
[object model](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects):

* each Git repo is an object store, mapping SHA1 to an immutable chunk
  of data and a type
* files are stored as **blob** objects
* directories are stored as **tree** objects, which just map child name to
  an object-id (either a blob or another tree), plus a mode (chmod)
* **commit** objects reference parent commits, comments, and a tree object
* **tag** objects are GPG-signed blobs that reference a commit
* Git can store all of these objects "loose", one local file per object,
  in ``.git/objects/XX/XYZZ``
* or, it can "pack" many objects into a single file, in
  ``..git/objects/pack``, with zlib compression, inter-object deltas,
  and an index for fast access. Local packs are self-contained, but
  "thin packs" can have deltas that depend upon objects that aren't in
  the packfile (e.g. when you know the recipient of the packfile already
  has those objects).
* the Git repo also remembers **refs**, which map branch/tag names to a
  commit object
* ``git add`` is what adds blobs and trees to the store. It also updates
  an internal reference called the **index**, which always points at a
  tree object. ``git commit`` creates a commit object around that tree,
  adds it to the store, and updates a ref.

There are a lot of similarities between Git's immutable blobs and
Tahoe's immutable files: this will help us map one to the other.

When you run ``git push``, git runs a
[clever protocol](https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols)
that attempts to minimize the amount of data it has to transfer. First,
the receiving server tells the client about all the refs it already has.
Then the client runs a graph-reachability algorithm against the local
tree, to make a list of all objects that are reachable by the references
being pushed, but not reachable from the remote's current refs
(something like ``git rev-list MINE ^THEIRS``: this is not guaranteed to
be minimal, but in practice it works quite well). Then it builds a
single packfile with all of these objects, expressed as deltas against
objects it knows the remote end has access to (``git pack-objects
--thin``). Then it merely sends this packfile over the wire.

The remote end drops the packfile into the local object store (``git
index-pack`` or ``git unpack-objects``), then verifies that it can find
all the new refs it's been sent (and every object they can reach). If
that looks good, it updates the ref to whatever the client specified.
Later, a ``git checkout`` or a pull can rely upon the routine that reads
objects from ``.git/objects/`` (using packfiles if necessary) to take
care of the rest.

A similar routine happens when ``git fetch`` pulls objects from a remote
repo.

Git remote helpers can do whatever they want, as long as the right
objects wind up in the right place.

Finally, for clarity, let's distinguish between the different kinds of
objects we're dealing with:

* **source files**: the files from the original workspace, which you
  manipulate with your editor or other application, and add with ``git
  add``
* **git objects**: the blobs and trees and commits that git knows about
* **tahoe objects**: CHK (immutable) and SSK (mutable) tahoe files and
  directories

## Efficiency

So we need to build a tool that maps the Git object graph (or changes to
it) into the Tahoe filesystem, and back again. Clearly we have a large
design space for this tool. There are several things we might try to
optimize or achieve:

* size of data (in bytes) pushed into Tahoe for each change
* number of objects added to Tahoe for each change
* rate of Tahoe garbage (dereferenced tahoe objects) generated per
  change
* amount of overhead (garbage-collection / consolidation work) done
  during push
* number of objects fetched by up-to-date subscribers for each change
* size of data fetched by subscribers
* number of objects / size of data fetched by new clones who care
  about getting the whole history
* same, for new shallow clones (those who don't care about history)
* does regular Tahoe garbage-collection work? or do we need a special
  tool to decide when it's safe to delete a Tahoe object?
* **direct representation**: does the Tahoe-side object graph look just
  like the Git-side graph?
* do we store all history? or just enough for the known subscribers?
* implementation complexity

The optimizations will depend upon the file sizes we're storing, how
they change over time (tiny edits or major modifications), and how
quickly we make changes to them. They'll also depend upon the clients:
do we need to support a lot of history for clients that sync
infrequently, or can we ignore history altogether? Some choices will
make the uploads cheaper at the expense of downloads, or vice versa.

Storing the entire history gives clients more information to perform
merges. We can reduce the storage requirements by not retaining any
history, but then clients who see conflicting local changes may have
less information to work with. If we know how up-to-date each client is,
we can get away with less information.

One use case is for a "todo" list, shared between a desktop and a
laptop. In this case, the main todo file might be 1MB in size, and each
day we add a few hundred bytes to it. The additions are mostly
line-oriented, so Git's native merge routines are likely to work pretty
well.

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
also need enough information to get from 5->8 and from 8->21 (if the
stale clients ever reconnect).

## One CHK Per Object, Tahoe-style

Given the close relationship between Git objects and Tahoe's immutable
CHK files, the simplest *conceptual* approach would be to store each Git
object blob in a separate CHK file, store trees/commits/tags as
immutable directories, and put the refs as children of a top-level
mutable directory.

When translating Git trees into (immutable) Tahoe directories, we'd
store each child's "mode" in Tahoe's metadata. Commits could be rendered
similarly: comments, tree object, and parent commits would all be
expressed as specially-named "children". The translation must be
reversible, so we can get the same SHA1 out from the far side.

In this scheme, you could browse the entire history with just `tahoe
ls`, and `git log` would look a lot like `tahoe get
$COMMIT/parent-1/parent-1/comments`. You could even do a checkout with
`tahoe cp -r`! However none of the Git SHA1 identifiers would appear in
the Tahoe tree. Any operations that needed to compare SHA1s against the
stored data (i.e. the "what objects need to be pushed" step of the
smart-transport protocol) would need a translation table. This would map
CHK filecap to SHA1 or vice versa. We could build this cache locally,
and not store it in the Tahoe directory, however we couldn't translate
an arbitrary SHA1 into the corresponding Tahoe object without first
processing every single Tahoe object.

Our "fetch" tool will do a recursive traversal of the tahoe directory
space, starting with the ref, copying everything it walks into the local
Git repo (with ``git hash-object -w --stdin``), and pruning each time
the child link points at something which already exists in our CHK->SHA1
cache. When it finishes the walk, it allows the normal "git fetch" to
run against the local repo, where it ought to find everything it needs.

This would be pretty easy to describe, but is hard to implement, since
our tool must understand the internal Git object format, as well as
knowing the entire object graph. It is also maximally inefficient for
uploaders: Tahoe's per-file overhead would be paid for every file and
parent directory that was changed, as well as the commit itself. Making
a single byte change to a 1MB file would cause a whole megabyte to be
stored (and then downloaded on the other side), with no opportunity to
take advantage of the similarity between revisions. It would also upload
additional (smaller) files for the tree and the commit objects, tripling
the number of Tahoe upload operations (which are not as fast as we'd
like).

It's pretty good for downloaders who are grabbing single arbitrary
revisions, or are limiting themselves to specific directories. These
"browsing" clients can fetch exactly the commit and tree and blob they
need, without pulling anything else out of the Tahoe store.

But it's bad for the main use-case: downloaders who already have some
portion of the history (and just want to update to the current version),
or who want to retrieve the whole history. These folks must fetch lots
of nearly-identical blobs, with no deltas or compression to make things
faster (a full MB per commit, in our TODO-list example).

## One CHK Per Object, Git-style

Another variant is to store each blob/tree/commit object verbatim, in a
CHK file, and then stash these filecaps in a shared object directory,
named after their Git-side SHA1. This structure would look just like the
``.git/objects`` directory. 

It means we can't use `tahoe ls` as a history-navigation tool, but that
probably wasn't a big win anyways.

Fetch would do a traversal like above, except that the tool must parse
the Git object to figure out what child objects are needed. Instead of a
bi-directional translation function, we just need a unidirectional
function that takes a Git object (as bytes) and returns a list of child
objects that it references. The tool doesn't need to know what the
relationship is (commit->commit, commit->tree, tree->tree, tree->blob).
It just needs to know how to walk the graph so it can find all the nodes
that must be downloaded from Tahoe and copied into the Git object store.

This approach has the same efficiency problems as above.

## Just store .git in Tahoe

The simplest thing to *implement* would be to just store the whole
``.git`` directory in Tahoe. That would let us avoid parsing Git data
structures at all.

We could define our remote to point at a "bare" repo in a separate
(local) directory, then add a
[``post-update`` hook](https://git-scm.com/docs/git-receive-pack.html#_post_update_hook)
to do a ``tahoe cp --recursive`` after the push is complete. Git
conveniently only ever adds objects to the target directory; the only
mutation is to replace the ``refs`` files, and those are small.

Unfortunately Git is too clever when you push to a local filesystem, and
frequently stores loose objects instead of packfiles. In some cases it
knows it can hardlink the same loose object file instead of actually
making a copy, which is super efficient. But even when it can't, it
still prefers to avoid the computational overhead of generating a
packfile. There appears to be some heuristic involved: pushing a lot of
commits at the same time can create a packfile, but pushing a single
commit (where the new objects are loose in the source repo) seems to
push loose objects, not a packfile.

Storing a lot of loose objects into Tahoe is going to be inefficient,
both for the pusher and the later fetcher/cloner, due to Tahoe's
relatively-high per-file overhead. Making a one-byte change to a 1MB
file in the top-most directory will yield three new objects (a new copy
of the 1MB blob, a new tree object, and a new commit object), two of
which are probably very small. It would be nicer to combine all three
objects into a single tahoe upload.

In this scheme, ``tahoe ls`` would show you the same thing as regular
``/bin/ls`` on the local Git object store, and Tahoe doesn't need to
know much about Git's internals. It remains completely unaware of Git's
object graph.

Git avoids putting too many files in a single directory by sharding the
``objects/`` directory into 256 subdirs; this structure would be
replicated in the Tahoe directory. For the "objects/" subdir, we could
use a whole bunch of mutable directories, or stick to a tree of
immutable directories (with a single mutable at the top). For "refs/",
it'd be best to have a tree of immutables with a single mutable root, so
that a coordinator daemon can watch just the one "refs/" directory for
changes (which should happen exactly once per push). Then we necessarily
have a mutable container directory, for which the dircap goes into the
Git URL.

## One-packfile-per-push

So to improve efficiency, we'd like to have one packfile for each push,
and never see loose objects in the Tahoe directory.

To force the creation of a new packfile for each push, we'd need our
helper program to pretend to be a remote repo, even though it's really
being stored on the same local disk as the original, as if we were doing
ssh-to-self. The actual implementation wouldn't use ssh, but could just
run a local copy of ``git receive-pack``, just like the ssh remote would
normally do on the target host.

We could either ``tahoe cp -r`` the resulting directory, or use FUSE to
mount the local directory into a Tahoe dircap (perhaps with `sshfs`).
The resulting tahoe objects would look the same. Using FUSE would reduce
the total disk space used (one local copy of each object, instead of
two), but FUSE isn't an option on all platforms (it may require root
access, and kernel support). Also, ``git receive-pack`` assumes it has
fast read access to it's "local" disk, so FUSE may be slower than
keeping an extra (cached) copy of the packfiles and indices.

Basically each time our helper is told to push something, it should
build a packfile that contains every object that isn't already in the
remote, which means each object that we don't remember pushing before.
This packfile can use the previous value of the ref as a basis (storing
deltas against those objects instead of complete copies, when that
helps).

This is pretty efficient for the uploader (although "thin" packs would
make it better, see below), as we do one Tahoe upload (the packfile) per
change, plus a mutable write to the Tahoe object that contains the refs.
For our 100-byte change to the 1MB TODO file, this will add a Tahoe
object slightly larger than 1MB for each commit.

It is similarly efficient for a subscriber, which reads the one packfile
for each revision.

However new clones have to read all the packfiles, which is roughly 1MB
per revision, and grows linearly with the size of history. This loses
out on the compression opportunities we could get if we could merge the
packfiles all together.

### Implementation Details

So we want something like ``tahoe cp -r``, except that most of the
source files will already be present in the target Tahoe directory.
``tahoe backup`` uses a database to remember what it's written before,
to avoid duplicate uploads, and compares filenames and sizes to predict
equality, but it also retains old snapshots (as behooves a backup tool).

In this case, we know that Git behaves in a specific way: it never
modifies a non-tempfile in the objects/ directory, and most filenames
are based on a hash of the contents. So we probably need a new tool,
which can take advantage of Git's constraints to efficiently map the
object store into a Tahoe directory:

* ignore tempfiles (these should be cleaned up by the time the tool runs
  anyways)
* for all filenames in the source that are also in the destination,
  assert that their filesizes are the same, then skip them
* copy all new files, creating CHK immutables for them
* this will include both .pack and .idx files, although we could
  probably omit the index (see below)
* update refs/ (which can hopefully be stored as LITs)
* finally, delete any files that don't exist in the source: this will be
  the result of a GC

This tool will have an outgoing Git ``objects/`` and ``refs/`` directory
to copy from, and a Tahoe dircap to copy into.

On the download side, the tool will have a dircap to read from, and a
pair of Git directories to write into. Once it finishes populating them,
the usual Git "smart" protocol can be allowed to "pull" from the local
copy.

The easiest thing to do is to assume that all packfiles are necessary:
the downloading client can list them all, then feed all the new .pack
files into ``git index-pack``. That will copy the .pack into the local
``objects/`` cache, check connectivity of all objects, and finally build
a new index file (so we could probably avoid storing them in the first
place).

The downside is that shallow clones, which don't care about history,
only need the most recent packfile, and without the indices (and code
that knows how to parse them), we can't tell which one that might be.

## Storing "thin" packs

If we're only changing one byte of a 1MB file, the need for packfiles to
be self-contained forces us to store the other 999999 bytes that weren't
changed. But Git's online protocol knows how to avoid this: it can
create a "thin" packfile, in which the new blob object is recorded as a
delta against some other blob that isn't in the packfile. It knows the
recipient has the old object, so it can reference it safely.

So if we have accurate information about what's already in the
tahoe-side repo, we can ask Git to create a thin pack (by piping object
references into ``git pack-objects --thin --stdout``), and store the
result as a tahoe file.

These thin packs are not acceptable residents of a
``.git/objects/pack/`` directory: Git insists that everything in the
local object store is self-contained. They normally only exist as a
stream, coming out of ``git pack-objects --stdout`` on one side of a
push, and being consumed by ``git receive-pack`` or ``git index-pack``
on the other. But we can define the Tahoe directory to contain something
other than a normal Git object store: it represents a frozen copy of
what would have been sent over a wire, like how you might replace a
network link with a hand-delivered parcel of disk drives.

This reduces our new tahoe files to just the delta between revisions
(plus the tree and commit objects). For adding 100 bytes to a TODO file,
the packfile will be 100 bytes long (plus maybe 100 bytes for the other
objects), minus any zlib compression savings. Removing 100 bytes is even
cheaper.

## One-packfile-per-client-delta

So far, we're creating one packfile per push. If we're doing the
Dropbox-like thing and committing each time inotify tells us something
has changed (ideally once per application-level "Save" command), we'll
get a constant stream of one-file-changed commits, and one push per
commit. This is ideal for live downloading clients, who already have the
previous state and want a cheap update operation. But new clones must
fetch a large number of (small) Tahoe files to complete their history.
Stale clients will also need to fetch a lot of files.

We can improve this by being aware of what our downstream clients
currently know, and consolidating adjacent packfiles when nobody needs
to (efficiently) read the intermediate state. The most efficient thing
possible for full-history downloaders (subscribers and new clones) would
be to have one packfile per old client version. In our example with
clients at versions 5, 8, and 21, we would need a "0->21" packfile (for
new clones), a "5->21" packfile (in case that version-5 client wakes up
and needs to update), and an "8->21" packfile (for the version-8
client). That doesn't minimize the tahoe-side *storage* (since we're
storing multiple copies of the same data), but it does minimize the work
that downloaders have to do.

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
while, we'll want to consolidate or "repack", replacing all the
one-change packfiles with a single many-change packfile. If there are
any stale clients, this packfile should go from the least-stale client's
last-known version, to the current version. If there are no stale
clients, it should just contain the entire history (0->current).

This incurs a certain amount of overhead for the periodic consolidation,
causing ``git push`` to take longer than usual, and creating tahoe-side
garbage (as the old small-packfiles are removed from the tahoe
directory). It also requires the consolidation process to be aware of
the subscribing clients. Normal ``git push`` doesn't need this
knowledge, only the occasional repack. This should probably be driven by
the synchronization daemon rather than the git-remote helper itself.

## Other Optimization Targets

Specific optimization goals would prompt the use of alternate (mutually
exclusive) strategies, each at the expense of other goals.

To optimize strictly for uploader bandwidth, we would upload a single
packfile per push, which contains just the new objects, expressed as
deltas against objects that are already present in the old commit. This
is also optimal for live subscribers, but new clones and stale clients
must fetch O(commits) objects to catch up, and the storage costs will
grow similarly.

To achieve a "direct representation" (where standard Tahoe CLI commands
can show you the git tree), each push must write a full copy of each
modified git object into a separate Tahoe object. This minimizes the
bytes fetched by random-access ("browsing") clients, but maximizes the
number of tahoe objects that must be downloaded (increasing the per-file
overhead). And it is seriously inefficient for regular subscribers.

To optimize strictly for storage consumed, we would have exactly one
packfile (with all history) at all times: each push replaces it with a
new (slightly larger) one. This is optimal for new clones, but
worst-case for live subscribers, who must fetch O(reposize) each time.
It's pretty bad for stale clients too, depending upon how stale they
are. And it creates tahoe garbage at a tremendous rate.

To optimize for stale subscribers, we would store one packfile per known
stale-client version (which brings that version up to the present). Live
subscribers are just "stale" at version N-1. This is fine for uploaders
if all subscribers are live, but gets worse as you add stale clients,
and even worse as those clients get more stale, something like
O(commits^2). Storing just the inter-client deltas is a reasonable
compromise. Occasional "repack" consolidation is probably a good idea.

## Existing Tools

Why do this at all? Can we achieve our goals with existing tools?

Tahoe's reliability comes from redundancy: spreading the data across
multiple servers, so you can tolerate the loss of some of them. Git
natively lets you achieve plain replication, by just pushing your data
to multiple git servers. Tahoe uses erasure-coding, which gives a better
robustness-per-expansion ratio than plain replication. But it's fair to
argue that the complexity of using Tahoe is greater than the robustness
improvement we get from its erasure-coding.

Tahoe's security comes from encrypting all data before it leaves the
client, and integrity comes from including hashes in the filecaps.
[git-remote-gcrypt](https://spwhitton.name/tech/code/git-remote-gcrypt/)
provides a remote-helper which encrypts data before sending it to a
remote git server. git-remote-gcrypt uses GPG and requires coordination
between GPG keys on all clients, in addition to having access rights to
a shared backend Git repository. I'm not a big fan of GPG, but in my
quick scan of the code, the approach looks sound. It appears to achieve
one-packfile-per-push, which is great.

It uses a single shared repository, however Git provides the equivalent
of locking, so clients aren't in danger of losing data when simultaneous
writes happen. Encryption is not convergent, so using the
one-write-repo-per-client topology described above will cause a few
rounds of redundantly-encrypted identical plaintexts to bounce around
before things settle down. While the backend is a git repository, it
does not use history in the normal Git way (there is only one commit,
which is replaced wholesale on each push), so the ciphertext cannot be
replicated with a plain "git pull".

Adding a new client with git-remote-gcrypt requires the new client be
given write access to the git repo, and ensuring data is encrypted to
the new client's GPG key. The simplest workflow is to give the new
client a shared SSH private key (for repo access) and a shared GPG
private key (for data decryption). It's also possible to copy the new
client's SSH pubkey to the server (.ssh/authorized_keys), and copy their
GPG pubkey to the other clients, but some old client must then upload a
new version before the new one can read anything. In contrast,
git-over-tahoe clients could be configured with just a dircap (assuming
Tahoe was already configured).

[git-annex](https://git-annex.branchable.com/) lets you store selected
git files in a separate location, rather than including them directly
inside the git repository. It has several modes, includine one which can
put these files into Tahoe. However the main git repo is neither
encrypted or redundant. I'm still looking for a way to take advantage of
git-annex for this use case.

## Synchronization Daemon, Membership Management

Once we have a git-over-tahoe tool implemented, with reasonable
performance and efficiency for our expected use cases, we'll need a
daemon to drive it. The purpose of using Git is to allow this daemon to
manage conflicts better: git can be configured to manage merges however
you like, including refusing to merge at all. Dropbox itself doesn't
merge anything, but instead shows you both copies (yours and theirs),
and you use renaming and deleting to express your preferred solution.
With Git you can look at all three copies (yours, theirs, and the common
ancestor), which gives you more information to work with.

This daemon will need a way to ask Tahoe to notify it about remote
changes in the other client's outbound directories (maybe a ``tahoe
watch DIRCAP`` command). It should use inotify/fsevents to watch the
local filesystem, to trigger a `git add/commit/push` cycle. This could
be made more accurate with a pass-through FUSE filesystem that can tell
when an application still has a file open for writing: nothing should be
committed to git until the save process is complete.

I'll examine this daemon more in a later blog post.
