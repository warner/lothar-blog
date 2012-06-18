:title: new kernel options
:date: 2005-10-29 14:04
:category: 

I'm in the process of upgrading my systems to linux-2.6.14, and noticed a
couple of neat patches that made it into the kernel this time around.

One is that FUSE (http://fuse.sourceforge.net) has finally gotten in. One
thing I'd like to use this for is setting up a UML-based jail, to limit the
authority of applications to the minimum necessary. Each app would get a
separate jail. The guest code runs in a virtual kernel that has read-only
access to things like /bin and /usr/lib (so system administration isn't a
nightmare, plus you don't have to have multiple copies of your base system,
plus memory-mapped libraries like libc.so can be shared amongst *everything*
in the system rather than each kernel keeping its own copy around). The jail
would then have a private read-write copy of everything it's supposed to have
read-write (say /tmp and /var).

The nice thing about this approach as opposed to the usual
big-file-as-block-device scheme that usually gets used with UML is that you
can look into the filesystem from the outside. If you want to see what
exactly the program has changed on its "disk", you just diff -r their
workspace with a checkpoint that you cp -r'ed out earlier. In contrast, the
fake-block-device approach requires that you *log in* to the guest system and
examine it from the inside, and if you assume that a malicious program has
already compromised as much as it can from the inside, you may no longer be
able to trust the tools that you would use to perform the comparison.

Of course, you still have to trust that the guest code is unable to
compromise the UML kernel, otherwise it now has control of a local user on
the host system, and may be able to bootstrap that upwards. But it limits the
immediate danger of a root compromise within the guest system, and allows for
better monitoring of the jail.

And you still need to patch the host kernel with the SKAS patch
(http://www.user-mode-linux.org/~blaisorblade/) because, while the necessary
arch-specific code to create a UML guest kernel has been merged into the
linux source, the changes that enable fast and safe UML operation in the host
have not.

The other neat feature that just showed up is CONFIG_SECCOMP. From the blurb:

 Once seccomp is enabled via /proc/<pid>/seccomp, it cannot be disabled and
 the task is only allowed to execute a few safe syscalls defined by each
 seccomp mode.

The idea is that you have a parent process that opens up a couple of pipes to
itself, forks off the child, then throws the child into seccomp mode. After
that, the child relies upon RPC over those pipes to make requests of the
parent. In this way, you get to run compiled languages at full speed, but
they are dependent upon an external entity to actually *do* anything. The
parent process can then grant capabilities to the child. Someone at the
cap-talk meeting at HP mentioned an approach like this about a month ago,
somebody had speculated about setting up an SELinux policy that prohibited
all syscalls except read(), write(), and select(). It appears that
CONFIG_SECCOMP does exactly this without requiring a full SELinux setup.
(although SELinux might be trivial to set up.. I've never tried).

SECCOMP comes from Andrea Archangeli, who is using it to provide exactly
these sorts of services on a pennies-per-CPU-second basis
(http://www.cpushare.com), using a bunch of Twisted-based code, no less.

Less exciting: CONFIG_CONNECTOR, which makes it easier to write kernel-side
event-driven interfaces that userspace can access through normal
socket/bind/send/recv/poll calls (via special netlink sockets). I've built
interfaces like this through magic /dev/foo files, but you have to build up
your own queueing routines, and implementing the necessary poll() hooks is a
nuisance. This unifies everything into an existing event-oriented interface,
so things like /dev/foo can stick to synchronous "give me the current state
*now*" -style applications. Also RELAYFS, which creates a filesystem
interface for efficiently transferring large streams of data from userspace
to kernelspace.

Also of interest to me: netfilter's netlink-socket interface has been
unified, so the IPv4-only ipt_ULOG target is turning into an all-protocol
NFNETLINK target. This is also intended to replace the syslog-based ipt_LOG
target. Queueing packets to userspace is being changed the same way, with the
more-flexible TARGET_NFQUEUE. Finally the kernel interface allows multiple
queues to userspace, which addresses some of the traffic-control problems
inherent to multiple kinds of traffic all sharing the same queue.

Plus, the ieee80211 code made it into the kernel, so I don't need to keep
building a separate module for my laptop's ipw2200 driver. And HOSTAP is now
in the kernel, for my PCMCIA prism2 card.
