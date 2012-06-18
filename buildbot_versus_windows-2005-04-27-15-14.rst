:title: buildbot versus windows
:date: 2005-04-27 15:14
:category: 

I just spent several hours getting a reasonable python environment working
under Windows, something I had hoped to never have a need for. The Buildbot
is having some.. disagreements.. with Windows, and it became clear that being
able to reproduce the problem locally was the only sane way to fix it.

Man, was that painful.

For the record, here's what I did. Many thanks to Bear for creating this
checklist and walking me through the process::

 0. Check to make sure your PATHEXT environment variable has ";.PY" in 
 it -- if not set your global environment to include it.
 
  Control Panels / System / Advanced / Environment Variables / System variables
 
 1. Install python -- 2.4 -- http://python.org
 	* run win32 installer - no special options needed so far
 
 2. install zope interface package -- 3.0.1final -- 
 http://www.zope.org/Products/ZopeInterface
 	* run win32 installer - it should auto-detect your python 2.4
           installation
 
 3. python for windows extensions -- build 203 -- 
 http://pywin32.sourceforge.net/
 	* run win32 installer - it should auto-detect your python 2.4 
           installation
 
  the installer complains about a missing DLL. Download mfc71.dll from the
  site mentioned in the warning
  (http://starship.python.net/crew/mhammond/win32/) and move it into
  c:\Python24\DLLs
 
 4. at this point, to preserve my own sanity, I grabbed cygwin.com's setup.exe
    and started it. It behaves a lot like dselect. I installed bash and other
    tools (but *not* python). I added C:\cygwin\bin to PATH, allowing me to
    use tar, md5sum, cvs, all the usual stuff. I also installed emacs, going
    from the notes at http://www.gnu.org/software/emacs/windows/ntemacs.html .
    Their FAQ at http://www.gnu.org/software/emacs/windows/faq3.html#install
    has a note on how to swap CapsLock and Control.
 
  I also modified PATH (in the same place as PATHEXT) to include C:\Python24
  and C:\Python24\Scripts . This will allow 'python' and (eventually) 'trial'
  to work in a regular command shell.
 
 5. twisted -- 2.0 -- http://twistedmatrix.com/projects/core/
 	* unpack tarball and run
 		python setup.py install
 	Note: if you want to test your setup - run:
 		python c:\python24\Scripts\trial.py -o -R twisted
 	(the -o will format the output for console and the "-R twisted" will 
          recursively run all unit tests)
 
  I had to edit Twisted (core)'s setup.py, to make detectExtensions() return
  an empty list before running builder._compile_helper(). Apparently the test
  it uses to detect if the (optional) C modules can be compiled causes the
  install process to simply quit without actually installing anything.
 
  I installed several packages: core, Lore, Mail, Web, and Words. They all got
  copied to C:\Python24\Lib\site-packages\
 
  At this point
 
    trial --version
 
  works, so 'trial -o -R twisted' will run the Twisted test suite. Note that
  this is not necessarily setting PYTHONPATH, so it may be running the test
  suite that was installed, not the one in the current directory.
 
 6. I used CVS to grab a copy of the latest Buildbot sources. To run the
    tests, you must first add the buildbot directory to PYTHONPATH. Windows
    does not appear to have a Bourne-shell-style syntax to set a variable just
    for a single command, so you have to set it once and remember it will
    affect all commands for the lifetime of that shell session.
 
   set PYTHONPATH=.
   trial -o -r win32 buildbot.test
 
  To run against both buildbot-CVS and, say, Twisted-SVN, do:
 
   set PYTHONPATH=.;C:\path to\Twisted-SVN
