#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
HOME = os.getenv('HOME')

def make_plot(root,domain,sc,time,Sprop,Vprop):
   """
   construct and render the plot
   time = hour in UTC
   """
   temp = '/tmp/testing.svg'
   f_out = '/tmp/awesome.png'

   fname = f'{root}/{domain}/{sc}/template.svg'
   full_svg = open(fname,'r').read()
   modified = full_svg.replace('XXdomainXX',domain)
   modified = modified.replace('XXscXX',sc)
   modified = modified.replace('XXtimeXX',time)
   modified = modified.replace('XXSpropXX',Sprop)
   modified = modified.replace('XXVpropXX',Vprop)

   with open(temp,'w') as f:
      f.write(modified)

   com = f'inkscape -b "rgb(0, 0, 0)" {temp} -e {f_out}'
   com += ' > /dev/null 2> /dev/null'  # silence
   os.system(com)


if __name__ == '__main__':
   root = HOME + '/Documents/RASP/PLOTS'
   domain = 'd2'
   sc = 'SC4+3'
   time = '12'
   Sprop = 'cape'
   Vprop = 'blwind'
   make_plot(root,domain,sc,time,Sprop,Vprop)
