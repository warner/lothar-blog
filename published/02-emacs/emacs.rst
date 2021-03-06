:title: emacs
:date: 2005-04-18 02:13
:category: weblog
:slug: 2-emacs

I set up a few tools to post blog entries from emacs. All entries are kept in
CVS, and the whole tree is rsync'ed over to the web server. The elisp which
actually publishes the entry looks like this::

  (defvar pyblosxom-entry-dir "~/stuff/Projects/WebLog/entries")
  
  ;; adapted from http://wiki.woozle.org/BlogdorEngine
  ;; and http://list-archive.xemacs.org/xemacs/200211/msg00022.html
  
  (defun char-isalpha-p (thechar)
    "Check to see if thechar is a letter"
    (and (or (and (>= thechar ?a) (<= thechar ?z))
  	   (and (>= thechar ?A) (<= thechar ?Z)))))
  
  (defun char-isnum-p (thechar)
    "Check to see if thechar is a number"
    (and (>= thechar ?0) (<= thechar ?9)))
  
  (defun char-isalnum-p (thechar)
    (or (char-isalpha-p thechar) (char-isnum-p thechar)))
  
  
  (require 'cl-seq)
  
  (defun blog-publish ()
    "Publish the blog entry in the current buffer"
    (interactive)
    (shell-command (format "cvs commit -m 'blog entry' %s"
                           (file-name-nondirectory buffer-file-name)))
    (shell-command "make -C .. publish")  ; publish
  )
  
  (define-minor-mode pyblosxom-post-minor-mode
    "Minor mode for blog posts"
    nil
    " blog-post"                          ; mode-line indicator
    '(
      ("\C-c\C-c" . blog-publish)
      )
    ()                                    ; forms run on mode entry/exit
  )
  
  (defun blog-post (title)
    "Create a journal entry"
    (interactive "sTitle: ")
    (let ((filetitle (substitute-if-not ?_
                                        (lambda (c) (char-isalnum-p c))
                                        title)))
      (find-file (concat pyblosxom-entry-dir "/"
                         filetitle
                         (format-time-string "-%Y-%m-%d-%H-%M")
                          ".txt"))
      (goto-char (point-min))
      (insert title "\n\n")
      (save-buffer)
      (vc-register)
      (pyblosxom-post-minor-mode 1)
  ))

