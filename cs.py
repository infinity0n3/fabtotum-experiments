#!/bin/env python

code = "N1 M105*"
cs = 0

for c in code:
  if c != '*':
    cs = int(cs) ^ ord(c)
    print "cs: {0}, c: {1}".format(cs, ord(c))

cs = cs & 0xff

print cs

