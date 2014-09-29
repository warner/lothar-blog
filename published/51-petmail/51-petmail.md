Slug: 51-petmail
Date: 2014-09-28 19:47
Title: Petmail, an introduction
Category: petmail

[Petmail](https://github.com/warner/petmail) is a secure-communications project I've been noodling at for a couple of months now. To be honest, I guess I've been noodling at it for over a decade: this latest effort is really a reboot of a [project](http://petmail.lothar.com/) that I did ten years ago, and [presented](http://petmail.lothar.com/CodeCon04/index.html) ([audio](https://archive.org/download/codecon2004audio/CodeCon_2004-02-21_4.mp3)) at a conference named [CodeCon04](http://web.archive.org/web/20110722174725/http://www.codecon.org/2004/) (which was also the venue for one of the early Tor presentations). My original Petmail was about spam-resistant secure email-like messaging.

I decided to re-use the name because my latest project has been converging with that old one. I'm not paying so much attention to the spam problem this time, but it's still about establishing a cryptographic connection between two people's user agents, and using that connection for messaging of various sorts.

## What (the heck is Petmail)?

First off, Petmail is still just a testbed: you can't actually do anything with it yet. Even if it passes the unit tests on your computer, it will probably steal your dog and eat all your ice cream. Don't give it the chance. If you foolishly checked out the repo from `https://github.com/warner/petmail.git` , my best advice to you is to delete it before it grows. You've been warned.

But, what Petmail aspires to be (some day) is a secure communication tool. By "communication" I mean to start with moderate-latency mostly-text point-to-point queued message delivery (like email). Then I want to add low-latency conversations (like IM), and some form of group messaging.

I'd also like to include file sharing, in several modes. The simplest is share-with-future-self (aka "backup"). The next is share-with-other-self (aka Dropbox). Then there's share-with-other (what most people think of as "file sharing"). I might try to incorporate share-with-world ("publish"), eventually.

By "secure", I mean that at the very least, an eavesdropper does not get to learn the contents of your conversations or that of the files you are storing/sharing. I also want forward-security, meaning that if your computer (and all of its secrets) gets stolen tomorrow, then we can limit what the thief learns about your conversations from yesterday. Deleting a message from your UI should actually delete it from your computer, not merely hide it from view. This is surprisingly difficult.

I'm also interested in various forms of anonymity, pseudonymity, and relationship-hiding. These are expensive (they increase protocol complexity, reduce performance, and generally make deployment more difficult), so I haven't yet decided whether to include them or not. I'll be writing more about the tradeoffs involved in later blog posts.

## Why (am I doing this)?

This latest effort started as a [testbed](https://github.com/warner/toolbed) where I could experiment with new UI and setup ideas for [Tahoe-LAFS](https://tahoe-lafs.org/), specifically invitation-code -based key-management, the database-backed node structure, and the secure all-web frontend.

There are a lot of secure messaging tools being developed right now (the moderncrypto.org [Messaging](https://moderncrypto.org/mailman/listinfo/messaging) list is a good place to see them being discussed). I won't pretend that mine is any better. And I'll admit to a certain about of Not-Invented-Here syndrome, where I prefer my own tool because of the language it's written in, the protocols/UX/architecture it uses, or simply because I get to make whatever changes I like. Or because it's easier for me to understand and trust my own code than to read and study someone else's.

But I've found that the best way to explain the ideas in my head, to other people, is to implement them and show them the code. Especially when the ideas include the way that two people establish a connection. I think a lot of security tools, mine included, get stuck because they were unable to start with the end user's experience in mind. There's much to be said for asking people to pretend to perform some task (where we might expect security to matter), see what (possibly crazy) assumptions they make about it, and then search for ways to make those assumptions come true.

For example, when someone runs a local mail client like Thunderbird, and sees a message with a "From:" line that has a name they recognize, it's reasonable for them to assume that this message was really written by that person. And if you know anything about SMTP, you know that's incredibly false. Likewise it's fair to expect that typing a recipient's name into a new message, or choosing someone from the addressbook, will result in a message that's only actually visible to that one person. Both assumptions are reasonable (in that lots of people would hold them), but are not met by existing systems, because they're pretty challenging to provide. We probably need to change user's expectations, but if at all possible we should find a way to meet them, because that's (by definition) the most intuitive mental model they're likely to construct and act upon.

I think that improving the security of communication tools will require a couple of efforts, working together:

* study what users want to do, and how they want to express it
* build a framework in which most of that is possible
* expose the limitations as clearly as we can: teach users what's possible and what's not

This needs to be iterative and somewhat interactive. If we mandate that users are allowed to do impossible things (like expecting for-your-eyes-only security from a bare email address), then we'll never succeed.

One option is to compromise on end-to-end security to make those expectations work. For example, some systems use TLS to fetch the recipient's purported public key from the target domain's SMTP server. This has the advantage of being backwards-compatible with established email practice (i.e. you can still copy a familiar user@domain address off a business card), but adds both their server and the Certificate Authority roots to the reliance set.

I'm not too excited about that direction, and I'd rather leave it for other projects to explore. I'm more interested in how to teach folks to use a new model that *is* possible, even if it's different or not as immediately useful as the insecure system.

## How (does it work)?

The basic idea is that you have an agent (a long-running program) working on your behalf, on your computer or phone. You introduce your agent to the agents of your friends, either by having the agents talk directly to each other (scanning QR codes, NFC pairing, etc), or by mediating the connection through the humans (you and your friend exchange a short code displayed by your computer):

    agent1 <-> human1 <-> human2 <-> agent2

This latter approach also allows you to bootstrap the new Petmail connection from some pre-existing relationship, like email or IM. Doing it this way yields different security properties -- it's hard to be sure you've connected with a specific person when they aren't actually standing in front of you -- but I think the result is good enough to be useful, and we can add post-introduction verification steps to close the gap. "I want to talk securely (to a person I've never physically met)" is a common enough user request, but kind of impossible, and raises some really deep questions that can sharpen our design.

When the introduction process finishes, the agents will have shared keys that they can use for encrypting subsequent messages. They also receive directions on how to reach the other agent, to deliver those messages (either for human consumption, or with internal administrative traffic).

People will actually have multiple agents, one per phone or computer. You introduce your own agents to each other with the same tools as before, but with a "meet your sibling" flag that tells the agents to trust each other more thoroughly. Your cluster of agents can then collude: to make sure that you see exactly one copy of each message, or that a correspondent added with your phone is also available from your laptop.

My initial system uses a python-based daemon that runs on your computer, and you talk to it with a local web browser (the `petmail open` command instructs the agent to open a new browser tab with the UI). Eventually I'd like to port it to a browser extension, then maybe as a standalone [web app](https://developer.mozilla.org/en-US/Apps), because the [WebRT feature](https://developer.mozilla.org/en-US/Marketplace/Options/Open_web_apps_for_desktop) makes those easy to install directly to Windows/Mac/Linux/Android/FxOS (just like a native application, but I don't have to learn Windows or Mac programming tools). It might also be interesting to build a hosted form of Petmail, with the obvious security limitations that entails, as a stepping-stone to a local install.

## More Posts To Come

I have a slew of design choices to make and/or explain: I plan to write up the resulting tradeoffs as future blog posts:

* What is relationship-hiding, pseudonymity, anonymity, and how much can Tor help us? Hidden services, low- vs high- latency mix networks, PIR retrieval systems. Is it really possible to receive messages anonymously?
* Introduction protocols: how short can we make the code? What else do we need to make it secure?
* Deployment modes: can we combine the invitation code with a "click here to install" URL? Safely?
* Secure web UI: avoiding secret URL leaks, CSRF, and shared-origin attacks
* Mailbox servers: queuing messages for agents that are offline, but hiding sender identities from the server.
* Bundling Tor with your app?
* How to rent a mailbox server: enabling an economy of services.
* Backup tools and progress indicators: since you can't be fast, be transparent.
* Configurable storage backends
* As-secure-as-you-want-it filecap URLs: making Tahoe-LAFS filecaps useable by regular web browsers too.
