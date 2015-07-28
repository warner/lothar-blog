import os, sys, re

def find_seqnums(rootdir):
    for root, dirs, files in os.walk(rootdir):
        for fn in files:
            afn = os.path.join(root, fn)
            if fn.endswith(".rst"):
                for line in open(afn):
                    mo = re.search(r'^:slug:\s+(\d+)-', line.lower())
                    if mo:
                        yield int(mo.group(1))
                        break
                else:
                    #print >>sys.stderr, "no ':slug: NUM' in %s" % afn
                    continue
            if fn.endswith(".md"):
                for line in open(afn):
                    mo = re.search(r'^slug:\s+(\d+)-', line.lower())
                    if mo:
                        yield int(mo.group(1))
                        break
                else:
                    #print >>sys.stderr, "no 'slug: NUM' in %s" % afn
                    continue

seqnums = set()
for dirname in sys.argv[1:]:
    seqnums.update(find_seqnums(dirname))
max_seqnum = max(seqnums)
print "%02d" % (max_seqnum+1)
