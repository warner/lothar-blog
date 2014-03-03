:title: Emacs Trick of the Day
:date: 2008-05-28 18:15
:category: emacs
:slug: 35-Emacs-Tricks

There are a few million gems hidden inside emacs. The two that I ran into
most recently are:

C-x r m, C-x r b, C-x r l : these create named bookmarks, each of which
records the file that you're visiting and a position within that file. When I
need to hold my place while I looked elsewhere, I usually split the window
(C-x 2) and leave one of them fixed while I moved around in the other one to
find something. Then C-x 0 makes that window go away, leaving me in my
original position. But if you do that too deeply, the windows get too small.

C-x r m creates a bookmark, and the name defaults to the name of the file (so
if you only use one bookmark per file, you don't even have to type anything).
Then C-x r b jumps back to that bookmark. C-x r l lists all your bookmarks.

Bookmarks can also be persistent.

highlight-trailing-space: by setting this to 't', any trailing whitespace
will be highlighted in an ugly orange color that makes you want to delete it
right away. Darcs does the same thing when you're committing code (it shows
you a special "[_$_]" -like symbol to make you aware of the whitespace at
then end of the line), so I've been in the habit of deleting that whitespace
anyways.. even wrote a little python tool to find it all for me. With
highlight-trailing-space turned on, I get to see the whitespace as I'm
editing, so I can remove it earlier.
