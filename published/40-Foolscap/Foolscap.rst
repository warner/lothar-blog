:title: Foolscap-0.4.2 released
:date: 2009-06-20 12:59
:category: foolscap
:slug: 40-Foolscap

I've released foolscap-0.4.2 .. download it from
http://foolscap.lothar.com/trac . 
!END-SUMMARY!

I made the relase last week, and as usual
I've managed to not send out the announcement email yet. One reason for that
is that I wanted to blog about it first, and I've started using a
foolscap-0.4.2 -based tool to manage my blog, and I effectively got into a
circular dependency between the blog and the blog software, with the email
depending upon both.

The big new feature in this release is the "FooLscap APPlication SERVER", or
"flappserver". It's like twistd for foolscap, enabling non-programmers to
deploy pre-written tools without needing to write new code. twistd makes it
easy to create and launch things like a web server or FTP server. flappserver
makes it easy to create and launch a service which is accessed remotely via a
secure FURL. There is a corresponding "flappclient" which takes a FURL (and
some arguments) and does something with that service. The service runs as
whichever user started the server, and it's easy to daemonize the server and
run it in the background. Typically you'd start the server from a @reboot
crontab entry or /etc/init.d script or LaunchAgent.plist file.

Eventually flappserver will have a plugin mechanism, but for now it comes
with two remarkably useful basic services. The first is named "upload-file":
the client provides the file and basename, the server provides the directory.
It's like a write-only drop-box, accessed with a FURL. This is great for
buildslaves that need to drop a generated package into some world-visible
directory: the buildslave can touch that one directory and no others, and
there are no funny filenames or shell-escape tricks it can use to break out
of there.

The second service is named "run-command": the server controls everything
about the command: executable, arguments, and working directory. The client
just gets to push the button. It's like a remote-garage-door-opener for
program execution. Optionally, the client can pass stdin and get stdout,
letting you use it like a secure network pipe to a server that's run
on-demand, sort of like inetd but with actual security.

It is nominally possible to do this sort of thing over SSH, but you have to
start by creating a keypair for each purpose and add it to your
authorized_keys file, and then figure out what sort of command= option to add
to keep that key from being able to control your entire account (which
usually means writing a script to implement the exact functionality you *do*
want to offer), then hope that nothing they sent as an environment variable
will compromise your security, then give them the 600-plus--character-long
pubkey, then have them write a script which translates their input arguments
into some "ssh -i single-purpose-pubkey hostname args-for-processing"
command.

With a running flappserver, it's just:

 flappserver add ~/server upload-file ~/incoming  # returns FURL

flappclient --furl FURL upload-file foo.jpg

As a demo of what you can do with those two tools, I've started to update
this very blog's back-end Git repository over a flappserver-based connection.
The half-a-dozen computers that I use all have a copy of the "update my blog"
FURL (really the "run git-daemon in the blog entries directory" FURL). The
details are in the foolscap source tree, in doc/examples (in TRUNK, not in
0.4.2). More about this in the next post.
