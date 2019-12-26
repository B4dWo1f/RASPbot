#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import datetime as dt

def parser(inp):
   Sprops = ['blcloudpct', 'bltopwind', 'blwind', 'bsratio', 'cape', 'hbl',
             'hglider', 'mslpress', 'rain1', 'sfcwind', 'wblmaxmin', 'wstar']
   Vprops = ['bltopwind','blwind','sfcwind']
   days = ['hoy','mañana','pasado','al otro','lunes','martes','miércoles',
           'miercoles', 'jueves','viernes', 'sábado', 'sabado', 'domingo']
   inps = inp.split()   # split by space
   print(inps)
   Sprop = 'sfcwind'
   Vprop = 'sfcwind'
   day = 'hoy'
   hour = '12'
   # Try to parse day
   # Try to parse hour
   try: hour = int(inps[-1])
   except ValueError:
      try: hour = dt.datetime.strptime(inps[-1],'%H:%M')
      except ValueError:
         # Error in hour
         pass
   return Sprop, Vprop, day, hour

if __name__ == '__main__':
   inps = ['cape sfcwind hoy 8',
           'cape  hoy 8',
           'hglider sfcwind al otro 8a:0']
   for inp in inps:
      parser(inp)
