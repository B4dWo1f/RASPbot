#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
 This script should keep the pics_ids.txt file clean
"""

import os
import datetime as dt
here = os.path.dirname(os.path.realpath(__file__))

fname = here + '/pics_ids.txt'

all_lines = open(fname,'r').read().strip().splitlines()

now = dt.datetime.now().date()
keep_lines = []
for l in all_lines:
   date = l.split()[0]
   date = '/'.join(date.split('/')[-4:]).split('_')[0]
   date = dt.datetime.strptime(date, '%Y/%m/%d/%H%M').date()
   p_id = l.split()[-1]
   if (date-now).total_seconds() > 0: keep_lines.append(l)

with open(fname, 'w') as f:
   for l in keep_lines:
      f.write(l+'\n')
f.close()
