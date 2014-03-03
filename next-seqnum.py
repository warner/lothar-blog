import os, sys, re

next_seqnum = 0
for root, dirs, files in os.walk(sys.argv[1]):
    for fn in files:
        afn = os.path.join(root, fn)
        if fn.endswith(".rst"):
            for line in open(afn):
                mo = re.search(r'^:slug:\s+(\d+)-', line.lower())
                if mo:
                    next_seqnum = max(next_seqnum, int(mo.group(1)))
                    break
            else:
                raise RuntimeError("no :slug: in %s" % afn)
        if fn.endswith(".md"):
            for line in open(afn):
                mo = re.search(r'^slug:\s+(\d+)-', line.lower())
                if mo:
                    next_seqnum = max(next_seqnum, int(mo.group(1)))
                    break
            else:
                raise RuntimeError("no slug: in %s" % afn)
next_seqnum += 1
print "%02d" % next_seqnum
