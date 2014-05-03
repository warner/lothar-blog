
Think about the various persistent data stored in a modern browser:

* bookmarks
* history
* saved passwords
* form data (username, mailing address, credit-card number)
* theme/skin
* preferences
* extensions, extension preferences
* open tabs

You probably care about some pieces more than others. For each, you might be
most comfortable with storing them:

* local-only: not synced at all, only OS-level backups
* paired: synched between devices that were paired by bringing them together,
  backup comes from retaining at least one working device
* password-based (cold start) with no escrow
* hosted, but you expect the service to not look at your data
* hosted, and you expect the server to know/see/use your data

Values
------

Users value each category of data in different ways, along a couple of
different axes. One of them is "availability", closely related to
"integrity", and means you can get your stuff when you want it. "Safe and
sound", and "secure" are clustered terms. If you wanted to quantify this, you
could ask people to set a price (in dollars): if I offered you $1 in exchange
for resetting your browser's theme, would you accept it? $5? $100? How about
for erasing all your bookmarks?

Another is "confidentiality", the ability for other people to see your data,
and to have it associated with you. Would you accept $1 in exchange for
having your browser theme displayed next to your name everywhere you went,
knowing that the same information appeared in advertiser databases, FBI
files, the phone book, your neighbors local-resident list? How about the web
sites you visit? How about the login passwords you use?

Finally there is "sharability value": times when it's *more* valuable to have
certain data be public than private. The pictures you post on Flickr for the
world to see are a good example, or your blog. For these, the measure is how
much money you'd have to be paid to stop publication. If it would take at
least $100 to buy out your youtube video channel, then clearly it's worth
about that much to you (you might be willing to pay $100 for the ability to
publish that data).

So, given these values (which are different for everybody and for each type
of data, and change over time as circumstances and attitudes drift), what
sort of storage solution feels most appropriate? For some data, keeping
things secret is more important than keeping them available: you'd rather
lose that data than let somebody else see it. For others, the opposite is
true: photos of your children that you'd publish to the whole world if it
meant that you'd never ever lose them.

Another aspect is what sort of fallbacks or backups you might have. If I
break my cellphone while travelling, I can get a new one when I get home, and
then restore the contents from the backup on my home computer. It's a hassle,
and I won't have access to my phone numbers until I get home, but I feel
pretty confident that I can get my data back eventually.

don't
expect it to happen very often, and I prefer to keep my personal data on my
own machines, so I'm ok with the tradeoff.


Backups, Recovery
-----------------



I have confidence in local backups, and I'm annoyed by intrusive services, so
it's easy for me to swing to ephemeral/paired.

Application-level sync/profile-management as a replacement for functional
local backups, or to achieve multi-device consistency.

Source of authority: server/service has control and you hope they grant
access to you and not to others.

Expectations based upon training: you've never been offered some properties,
so you've never had cause to believe you might be able to get them, or
deserve them.

done:

#Availability value, confidentiality value. Measuring both in dollars, asking
#user to set a price. Sharability value: value obtained by making the data
#available to others.

