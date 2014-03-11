#!/usr/bin/env python

import os

with open('/temp/portalInfo.txt') as f:
    s = f.read()

first_line = s.split('\n', 1)[0]
fields = first_line.split('\t')

d = []

for line in s.split('\n'):
    d.append(dict(zip(fields, line.split('\t'))))

    
print d

