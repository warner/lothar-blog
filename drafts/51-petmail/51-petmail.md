Slug: 51-petmail
Date: 2014-09-22 23:40
Title: Petmail

[Petmail](https://github.com/warner/petmail) is a project I've been noodling at for a couple of months now. To be honest, I've been noodling at it for over a decade: this latest effort is really a reboot of a [project](http://petmail.lothar.com/) that I did in 2003, [presented](http://petmail.lothar.com/CodeCon04/index.html) ([audio](https://archive.org/download/codecon2004audio/CodeCon_2004-02-21_4.mp3)) at [CodeCon04](http://web.archive.org/web/20110722174725/http://www.codecon.org/2004/) where Tor was (first?) presented. The original Petmail was about spam-resistant secure email-like messaging.

I decided to re-use the name because my latest project has been converging with that old one. I'm not paying so much attention to the spam problem this time, but it's still about establish a cryptographic connection between two people's user agents, and using that connection for messaging of various sorts.

## What (the heck is Petmail)?

First off, Petmail is still just a testbed: you can't actually do anything with it yet. Even if it passes the unit tests on your computer, it will probably steal your dog and eat all your ice cream. Don't give it the chance. If you foolishly checked out the repo from https://github.com/warner/petmail.git , my best advice to you is to delete it before it grows. You've been warned.

But, what Petmail aspires to be (some day) is a secure communication tool. "Communication", starting with moderate-latency mostly-text point-to-point queued message delivery (like email). I also intend to include low-latency conversations (like IM), and some form of group messaging.

I also intend to include file sharing, in several modes. The simplest is share-with-future-self (aka "backup"). The next is share-with-other-self (aka Dropbox). Then there's share-with-other (what most people think of as "file sharing"). I might try to incorporate share-with-world ("publish") eventually.

By "secure", I mean that at the very least, an eavesdropper does not get to learn the content of your conversations or of the files you are storing/sharing. I also want forward-security, meaning that if your computer is captured tomorrow (along with all of its secrets), then the thief gets limited information about the content of your conversations from yesterday. Deleting a message from your UI should actually delete it from your computer, not merely hide it from view. This is surprisingly difficult.

I'm also interested in various forms of anonymity, pseudonymity, and relationship-hiding. These are expensive (i.e. increased protocol complexity, reduced performance, and more difficult deployment), so I haven't yet decided whether to include them or not. I'll be writing more about the tradeoffs involved in later blog posts.

## Why (am I doing this)?

This latest effort started as a [testbed](https://github.com/warner/toolbed) where I could experiment with new UI and setup ideas for [Tahoe-LAFS](https://tahoe-lafs.org/), specifically invitation-code -based key-management, the database-backed node structure, and the secure all-web frontend.

There are a lot of secure messaging tools being developed right now. I won't pretend that mine is any better. I'll admit to a certain about of Not-Invented-Here syndrome, where I prefer my own tool because of the language it's written in, the protocols/UX/architecture it uses, or simply because I get to make whatever changes I like. Or because it's easier for me to understand and trust my own code than to read and study someone else's.

But I've found that the best way to explain the ideas in my head, to other people, is to implement them and show them the code. Especially when the ideas include the way that two people establish a connection. I think a lot of security tools, mine included, get stuck because they were unable to start with the end user's experience in mind. There's a lot to be said for asking people to pretend to perform some task (where we might expect security to matter), see what (possibly crazy) assumptions they make about it, and then search for ways to make those assumptions actually true.

For example, when someone runs a local mail client like Thunderbird, and sees a message with a "From:" line that has a name they recognize, it's reasonable for them to assume that this message was actually written by that person. And if you know anything about SMTP, you know that's incredibly false. Likewise it's fair to expect that writing a new message and typing a recipient's name into it, or choosing someone from the addressbook, will result in a message that's only actually visible to that one person. Both assumptions are reasonable, but not honored by existing systems. We probably need to change user's expectations, but if at all possible we should find a way to meet them, because that's (by definition) the most intuitive mental model they're likely to construct and act upon.

I think that improving the security of communication tools will require a couple of efforts, working together:

* stuy what users want to do, and how they want to express it
* build a framework in which most of that is possible
* expose the limitations as clearly as we can: teach users what's possible and what's not

It needs to be somewhat interactive. If we mandate that users are allowed to do impossible things (like expecting for-your-eyes-only security from a bare email address), then we'll never succeed. We might compromise on security to make those expectations work (TLS to the email domain, some key-lookup protocol from that domain), but other projects are pursuing that direction, and it doesn't excite me so much. I'm more interested in how to teach a new model that *is* possible, even if it's different or not as immediately useful as the insecure system.

## How (does it work)?

The basic idea is that you have an agent (long-running program) working on your behalf, on your computer. You introduce your agent to those of your friends, either by having the agents talk directly to each other (scanning QR codes, NFC pairing, etc), or by mediating the connection through the humans (you and your friend exchange a short code displayed by your computer):

    agent1 <-> human1 <-> human2 <-> agent2

This latter approach also allows you to bootstrap the new Petmail connection from some pre-existing relationship, like email or IM. The security properties are different: it's hard to be sure you've connected with a specific person when they aren't actually standing in front of you, but I think the result is good enough to be useful. There are also post-introduction verification steps that we can add.

The introduction process gives the agents shared keys they can use for communication later. It also tells them how to reach the other agent, to deliver messages (either for human consumption, or internal administrative traffic).

People will actually have multiple agents, one per phone or computer. You introduce your agents to each other with the same tools as before, but with a "meet your sibling" note that tells the agents to trust each other more thoroughly. Your cluster of agents can then collude to make sure you see exactly one copy of each message, and that a correspondent you add from your phone is also available from your laptop.

My initial system uses a python-based daemon that runs on your computer, and you talk to it with a local web browser (the `petmail open` command instructs the agent to open a new browser tab with the UI). Eventually I'd like to port it to a browser extension, then maybe as a standalone [web app](https://developer.mozilla.org/en-US/Apps), because the [WebRT feature](https://developer.mozilla.org/en-US/Marketplace/Options/Open_web_apps_for_desktop) makes those easy to install directly to Windows/Mac/Linux/Android/FxOS like a native application. It might also be interesting to build a hosted form of Petmail, with the obvious security limitations that entails, as a stepping-stone to a local install.

## More Posts To Come

I have a slew of design choices to make and/or explain: I plan to write up the resulting tradeoffs as future blog posts:

* What is relationship-hiding, pseudonymity, anonymity, and how much can Tor help us? Hidden services, low- vs high- latency mix networks, PIR retrieval systems. Is it really possible to receive messages anonymously?
* Introduction protocols: how short can we make the code? What else do we need to make it secure?
* Deployment modes: can we combine the invitation code with a "click here to install" URL? Safely?
* Secure web UI: avoiding secret URL leaks, CSRF, and shared-origin attacks
* Mailbox servers: queuing messages for agents that are offline, but hiding sender identities from the server.
* Bundling Tor with your app?
* How to rent a mailbox server: enabling an economy of services.
* Backup tools and progress indicators: if you can't be fast, be transparent.
* Configurable storage backends
* As-secure-as-you-want-it filecap URLs: making Tahoe-LAFS filecaps useable by regular web browsers too.

