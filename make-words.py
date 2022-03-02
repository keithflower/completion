import pygtrie
import pickle
import time
import sys

t = pygtrie.CharTrie()

t = pygtrie.CharTrie()
t['wombat'] = True
t['woman'] = True
t['man'] = True
t['manhole'] = True

t0 = time.time()
f = open(sys.argv[1], 'r')
wl = f.readlines()

for wd in wl:
    t[wd.strip()] = True
t1 = time.time()

#print (t.items(prefix='cat'))

print ("time 1", t1-t0)

pickle.dump(t, open("save.p", "wb"), protocol=pickle.HIGHEST_PROTOCOL)

t0 = time.time()

newt = pickle.load( open ("save.p", "rb"))
t1 = time.time()

#print (newt.items(prefix='cat'))


print ("time 2", t1-t0)

# Add a word

t0 = time.time()
t['remdesivir'] = True
t1 = time.time()
print ("time to add a word", t1-t0)

print (t.items(prefix='remdes'))
