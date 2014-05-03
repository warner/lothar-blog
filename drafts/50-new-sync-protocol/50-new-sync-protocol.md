Slug: 50-new-sync-protocol
Date: 2014-03-25 18:05
Title: The new Sync protocol

(This wraps up a two-part series on upcoming changes in Firefox Sync, based on [my presentation](http://people.mozilla.org/~bwarner/warner-rwc2014/#/) at [RealWorldCrypto 2014](http://realworldcrypto.wordpress.com/). Part 1 was about problems we observed in the old system. Part 2 is about the system which replaces it.)

[Last time](../49-pairing-problems) I described the user difficulties we observed with the pairing-based Sync we shipped in Firefox 4.0. In late April, we released Firefox 29, with a new password-based Sync setup process. In this post, I want to describe a little bit about the protocol we use in the new system, and the security properties you can expect to get out of it.

(for the gory details, you can jump directly to the full [technical definition](https://github.com/mozilla/fxa-auth-server/wiki/onepw-protocol) of the protocol, which we've nicknamed "onepw", since there is now just "one password" to protect both account access and your encrypted data)

## New Requirements

To recap the last post, the biggest frustration we saw with the old Sync setup process was that it didn't "work like other systems": users *thought* that their email and password would be sufficient to get their data back, but in fact it really required access to a device that was already attached to your account. This made it unsuitable for people with a single device, and made it mostly impossible to recover from the all-too-common case of losing your only browser.

So the biggest new requirement for Sync was to make your data recoverable with just email+password.

We've retained the requirement that Sync data is end-to-end encrypted, using a key that is only available to you and your personal devices.

And finally, we're rolling out a new system called Firefox Accounts, aka "FxA", which will be used to manage access to new server-based features like the application marketplace and FirefoxOS-specific services. The third requirement was to make Sync work well with the new Accounts.

## Firefox Accounts: Login + Keys

So we designed Firefox Accounts to both support the needs of basic login-only applications, *and* provide the secrets necessary to safely encrypt your Sync data, while using traditional credentials (email+password) instead of pairing.

The login portion uses BrowserID-like certificates, with a "principal" of your GUID-based FxA account identifier. The secrets are provided by a pair of encryption keys.

### Encryption Keys

Each account has two encryption keys, which are used to protect two distinct classes of data.

Sync data falls into "class-B", and uses a key called "kB", which is protected by your account password. In technical terms, the FxA server holds a "wrapped copy" of kB, which requires your password to unwrap. To access any data encrypted under kB, you must remember your password. This means that anyone who *doesn't* know the password can't see your data.

If you forget the password, you'll have to reset the account and create a new kB, which will erase both the old kB and the data it was protecting. This is a necessary consequence of properly protecting kB with the password: if there were any *other* way for you to recover the data without the password, then a bad guy could do the same thing.

FxA also manages a second key named "kA", which can be used for "recoverable data". We don't have any applications which use kA yet, but we might add some in the future. This key is stored by the server without wrapping, so it can give the key back to you even if you forget the account password. As long as you can still receive email at the registered address, you can reset the account (to a new password) and get back "kA", along with any data encrypted under it. A necessary consequence is that an attacker who manages to compromise the auth server will learn kA too.

"kA" and "kB" are "root" keys: each application will get a distinct derivative key for their class-A and class-B . That way two applications which both use class-B data get different encryption keys, and they won't be able to decrypt data that was meant for the other application.

### Keeping your secrets safe

To make sure your class-B data really is tied to your password, we must avoid ever letting the server figure out your password. The first line of defense is that the server is never told your raw password: you must prove that you know the password, but that's not the same thing as revealing it. The client sends a hashed form of the password instead.

The second line of defense is that the protocol uses "key-stretching" on the password before sending anything to the server, to make it hard for the compromised server to even attempt to guess your password. This stretching is pretty lightweight (1000 rounds of PBKDF2-SHA256), but only needs to protect again the attacker who gets to see the stretched password in-flight (either because they compromised the server, or they've somehow broken TLS).

Finally, the data stored on the server is stretched even further, to make static compromises of the server's database less useful to an attacker. This uses a full second of the "scrypt" algorithm.

For full details, take a look at the [key-wrapping protocol specs](https://github.com/mozilla/fxa-auth-server/wiki/onepw-protocol) and the [server implementation](https://github.com/mozilla/fxa-auth-server).

## What Does It Look Like?

In FF29, when you set up Sync for the first time, you'll see a box that asks for an email address and a (new) password:

<img alt="FF 29 Sync Account-Creation Dialog" src="./create.png" width="270px" />

You fill that out, hit the button, then the server sends you a confirmation email. Click on the link in the email, and your browser automatically creates an encryption key (kB) and starts uploading ciphertext.

Connecting a second device to your account is as simple as signing in with the same email and password:

<img alt="FF 29 Sync Sign-In Dialog" src="./sign-in.png" width="270px" />

## Security Properties

Sync retains the same end-to-end security that it had before. The difference is that this security is derived from your password, rather than pairing. So your security depends upon having a good password: if someone can guess it, they'll be able to connect their own browser to your account and then see all the Sync data you've stored there. The best passwords are randomly generated.

The difficulty of making each guess depends upon what else the attacker has managed to steal. Regular attackers are lmited to "online guessing", which is rate-limited by the server, so they'll only get dozens or maybe hundreds of guesses. An attacker who gets a copy of the server's database (perhaps through an SQL injection attack, the sort you read about every month or two) have to spend about a second of computer time for each guess, which [adds up](http://keywrapping.appspot.com/) when they must try a lot of them. The most serious kind of attack, where the bad guy gets full control of the server and can eavesdrop on login requests, yields the "fast" offline guessing attack (PBKDF) which could be made cheaper with specialized hardware.

The security of old Sync didn't depend upon a password, because the pairing protocol it used meant there were no passwords.

## Conclusion

The new Sync sign-up process is now live and adding tens of thousands of users every day. The password-based process makes it possible to use Sync on just a single device: as long as you can remember the password, you can get back to your Sync data.
