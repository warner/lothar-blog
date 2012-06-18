:title: pyblosxom-noindex
:date: 2005-05-04 03:13
:category: weblog

After some amount of perseverance, I finally figured out how to make
pyblosxom insert "noindex" meta tags in the top-level index page. This was
the last barrier keeping me from linking this blog to the main site, since I
didn't want Google indexing a page that's going to change every few days
anyway.

For reference, here's the plugin I made. It's remarkably simple, after I
traced through the code for several hours to figure out what function needed
to be hooked::

  #! /usr/bin/python
  
  import sys
  
  template = \
  """<html>
  <head><title>$blog_title_with_path</title>
  <meta name="robots" content="follow,noindex" />
  </head>
  
  <body><h1>$blog_title</h1><p>$pi_da $pi_mo $pi_yr</p>
  
  """
  
  def cb_head(args):
      """This replaces the HEAD portion of the template whenever a 'directory'
      is being rendered. The modified template adds special 'noindex' meta tags
      to tell google that it shouldn't bother indexing the main page (since it
      will change), but to index the permalink pages instead.
      """
      #print >>sys.stderr, args['template']
      if args['request'].getData()['bl_type'] == "dir":
          args['template'] = template
      return args
