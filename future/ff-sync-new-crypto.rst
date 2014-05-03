Firefox Sync's New Crypto
=========================

Since its 2010 debut in Firefox 4, "Firefox Sync" has been powered by a
distinctive encryption system which ensures that you, and only you, have
access to the bookmarks, history, tabs, and passwords which it maintains
in-sync among all your devices. This system doesn't use passwords:
instead it creates a unique secret key, which is used to encrypt and
decrypt all your data: the only way to get at your data is to know this
key. Even the Mozilla servers which hold your data cannot decrypt the
contents.

You (almost) never see this key, known as the "recovery key", because
the normal way to set up a new device is with a technique called
"pairing". When you set up a new device, it shows you a 12-character
"J-PAKE pairing code", which you then type into the other device.
Through some crypto magic, the recovery key and everything else
necessary to set up Sync is safely copied to the new device. Now both
devices know the secret key and can talk securely about your bookmarks
and other data.

But in the last four years, we've seen a lot of problems with this
scheme. The biggest is that it doesn't do you much good if you only have
one device: pairing is about *pairs* (or threes or fours), and if lose
your only device, there's no way to get your data back. Pairing is not a
very common technique yet, and we've seen a lot of people get confused
when faced with the pairing code, thinking that it represented some sort
of computer-generated password that they were required to remember.

Enter Firefox Accounts
----------------------

This year, the Identity group is introducing "Firefox Accounts", which
will be used to access a variety of Mozilla services (like the app
Marketplace and the Where's My Fox phone-recovery system). These
accounts will be based around an email address and a password, just like
the hundreds of other account systems you're already familiar with.

We're changing Sync to use Firefox Accounts, instead of pairing. The
security goals remain the same: there is still a strong random secret
key, and the servers cannot decrypt your data. But instead of using
pairing to get this key from one device to another, the key is protected
by the password that you enter. This means you can recover all your
data, even if you've lost all your devices at the same time (or your
only phone breaks), by setting up a new device and typing your Firefox
Account email and password into it. The new device will connect to the
account and download all the saved encrypted data.

The security of your data now depends upon your password: if it is
guessable, then somebody else can connect to your account and see your
data too. So make sure you pick a strong password. The best passwords
are randomly generated.

For the technical details of the new encryption scheme works, check out
<this blog post> by the security engineers developing it.

The new system is scheduled to appear in Firefox 29, to be released on
April 29th. We hope you enjoy using it!
