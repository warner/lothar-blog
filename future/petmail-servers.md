Once upon a time, the Internet worked. A consumer device that was "connected
to the Internet" could generally be assumed to:

* have a stable, globally-reachable IPv4 address
* be capable of sending packets to arbitrary devices and ports
* be plugged into AC power
* be online 24/7

These days, none of these things are true. The largest class of
consumer-facing devices are smartphones, which have at least one layer of NAT
in front of them (sometimes two), are effectively turned off most of the
time, get shut down frequently and without notice, and are all but
unreachable even when they're powered on. They can make outbound TCP
connections, and occasionally UDP.

The next largest category is probably a laptop connected to a home network,
which means NAT, intermittent power, and frequently a firewall that prevents
all but outbound HTTP/TLS (and not even TLS, in certain countries). Serious
low-level protocol development has been all but abandoned as the potential
userbase dwindles.

The next largest class may be AC-powered desktop-style computers on a home
network. These could be online all the time, but the modern ones sleep
whenever they can, and all sorts are frequently turned off when their human
goes away. They are likely to be online slightly more often than a laptop
simply because the power button is further away.

Finally, the desktop-style computer in a datacenter (a "real server") is
probably the smallest class, despite being the foundation upon which all the
mobile devices depend. These have full (or at least deliberate) connectivity,
highly-reliable power, and are online 24/7.

## Reachability

There are a few tricks we can use to make a server reachable despite being
behind a firewall or lacking a public IP address:

* try to use UPnP (but it'll probably be broken)
* DHT-style hole-punching (with external coordination helpers)
* find a relay to help

A Tor "Hidden Service" falls into the last category: Tor relay nodes are
"real" servers, and will forward (encrypted) connections to your hidden
service as necessary. The downsides are that the sender must have a copy of
Tor available, the latency is worse, and the throughput is lower.

## Petmail server requirements

Petmail has three pieces:

* "mailbox server": receives messages for you when your agent is offline
* "agent": fetches messages from servers, sends messages to servers, delivers
UI and data to frontend
* "frontend": runs in a browser, presents UI, connects to agent

The mailbox server needs to be reachable by other agents, otherwise senders
won't be able to deliver their messages. The agent must be able to connect to
the servers to deliver those messages, and is assumed to be running most of
the time (so it can respond to acks and key rotation messages). The frontend
needs a safe HTTP connection to the agent, as well as a way to get an access
token.


## The Current Implementation

In my current implementation
(https://github.com/warner/petmail/48a712d8b0b6556dd608fbcb1d05178270ef3a8f),
the server and agent can run in the same process (in which case it needs a
public address), or in separate ones. The agent is launched as a long-running
daemon, and provides a localhost-only HTTP server that delivers the frontend.
The `petmail open` command must be run on the same host as the agent, and it
effectively reads an access token directly out of the agent's database. This
opens the frontend in a browser on the same host as the agent, where its HTTP
connection is safe because the packets only traverse the loopback interface
(and never leave the kernel).

Unfortunately, this is pretty limiting. It's really only suitable for running
on a desktop machine, where you can leave the daemon running for long periods
of time, with or without an externally-reachable network connection.

## How to make Petmail work for everybody

I'm running into a tension between development complexity and deployability.

If we callously define "everybody" as "people with an Apple or Android
smartphone", then we don't have a lot to work with. The short attention span
of the device makes it hard for an on-phone agent to participate in protocol
retransmits, and certainly precludes any sort of server functionality. Proper
end-to-end crypto means we don't want to run the agent anywhere else.

It's pretty easy to put an HTML UI into a smartphone app (think UIWebView),
and glue it to arbitrary agent logic, so I can probably share the UI code
between phone and desktop/laptop. With the right choice of language
(phonegap? some UI thing that ddahl was using), I can share the agent code
too. But then we might as well remove all the socket-listening code from the
agent; if phones are truly dominant, then those sockets won't help the
majority of users.

## Tor

For server-like things, Tor (in particular Hidden Services) enables
connectivity despite NAT and unrouteable addresses. This would let you run a
mailbox server at home, without manually configuring port-forwardings or
depending upon UPnP.

For client-like things, Tor lets you talk to those server-like things, and
hides your IP address from everybody, but doesn't really improve your
connectivity.

With enough packaging effort, I could probably include a copy of Tor along
with the real-computer (desktop/laptop) builds. There are builds of Tor for
(non-rooted) Android phones, which act as a proxy to protect all your
traffic, but I haven't heard of way to run a Tor hidden service on a phone,
especially not bundled into another app. And I expect both to be pretty
difficult on an iPhone. By the time Tor gets running (connected to directory
servers, establish circuits, etc), the app will probably be shut down
anyways.

So if we're running on a phone, then there must be some exterior server that
it will talk to without Tor (encrypted, but an eavesdropper can tell they're
communicating). That suggests a significant redesign, where the agent is
split into two parts:

* server-side: uses Tor, reachable, runs 24/7, talks to mailbox servers
* phone-side: talks only to server-agent, holds secrets

In one sense, this would look like an IMAP server, except that we don't want
the server-side to have anywhere near that sort of authority.

Previously, the mailbox server was only responsible for receiving messages.
If the agent connects to it over Tor, then the worst it can do is
selectively drop messages.

How much authority should this new server-half-agent get? What do we need
connectivity for?:

* acks: indicating that a message was successfully delivered, so the sender
  can stop worrying about it. Really this means the server has taken
  responsibility for the message ("this is now my problem, not yours").
* delivery/location information updates. when a client starts using a
  different set of mailbox servers, it sends updates to all correspondents
  about the change, and can stop listening on the old one when these updates
  have been acked. Similarly, agents may need to obtain "delivery tokens"
  from their mailbox servers, then distribute them to their senders. It may
  need to respond to requests for more tokens.
  
## Options

* 1: one process
* 1a: no Tor: limited to desktops/laptops with public IP, working UPnP, or
  manual port-forwarding. Reveals IP to everybody. Only usable when both ends
  are online, so IM and voice/videochat but not voicemail or async email.
* 1b: with Tor: Same use cases, but usable by NAT/non-public-IP too, and
  hides IPs.
* 2: two processes: 1=mailbox server, 2=agent/frontend. Obligates users to
  run/rent/borrow/beg/steal server space. Enables all use cases.
  Machine-to-machine traffic is trouble unless agent lives in a usually-on
  desktop machine. 2a= no Tor: reveals IP. 2b yes Tor: hides IP.
* 3: three processes: 1=mailbox server, 2=server-half-agent,
  3=client-half-agent/frontend. Obligates users to get both servers. Client
  half-agent is assumed to be intermittent. Protocol must shift acks and
  maintenance traffic to server-half-agent.
