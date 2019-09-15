#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
 This script should keep the pics_ids.txt file clean
"""

import os
import datetime as dt
here = os.path.dirname(os.path.realpath(__file__))

fname = here + '/pics_ids.txt'
t0 = 5*60*60  # if files send longer than t0 seconds ago, send the new version

all_lines = open(fname,'r').read().strip().splitlines()

now = dt.datetime.now()
keep_lines = []
for l in all_lines:
   date = l.split()[0]
   date = dt.datetime.strptime(date, '%d/%m/%Y-%H:%M')
   p_id = l.split()[-1]
   if (now-date).total_seconds() < t0: keep_lines.append(l)

with open(fname, 'w') as f:
   for l in keep_lines:
      f.write(l+'\n')
f.close()
