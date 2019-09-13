#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from telegram import ChatAction, ParseMode
import string
from urllib.request import urlretrieve
import datetime as dt
import aemet
import re
import logging
import os
HOME = os.getenv('HOME')
LG = logging.getLogger(__name__)
f_id_files = 'pics_ids.txt'

def call_delete(bot, job):
   chatID = job.context['chat']['id']
   msgID = job.context['message_id']
   bot.delete_message(chatID,msgID)

def send_picture(bot, chatID, job_queue, pic, msg='',
                 t=60,delete=True,dis_notif=False):
   """
    Send a picture and, optionally, remove it locally/remotely (rm/delete)
    pic = photo to send
    msg = caption of the picture
    t = time to wait to delete the remote picture
    delete = remove remote file t seconds after sending
    dis_notif = Disable sound notification
   """
   LG.info('Sending picture: %s'%(pic))
   if pic[:4] == 'http': photo = pic
   else:
      try: photo = open(pic, 'rb')  # TODO raise and report if file not found
      except: photo = pic
   bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_PHOTO)
   M = bot.send_photo(chatID, photo, caption=msg,
                              timeout=300, disable_notification=dis_notif,
                              parse_mode=ParseMode.MARKDOWN)
   if delete:
      LG.debug('pic %s to be deleted at %s'%(pic,dt.datetime.now()+dt.timedelta(seconds=t)))
      job_queue.run_once(call_delete, t, context=M)
   return M

def rand_name(pwdSize=8):
   """ Generates a random string of letters and digits with pwdSize length """
   ## all possible letters and numbers
   chars = string.ascii_letters + string.digits
   return ''.join((choice(chars)) for x in range(pwdSize))

def parse_time(time):
   try:
      pattern = r'(\S+):(\S+)'
      match = re.search(pattern, time)
      h,m = (match.groups())
      m = 0
   except AttributeError:
      h = time
      m = 0
   return int(h), int(m)


def parser_date(line):
   numday = {0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
             4: 'viernes', 5: 'sábado', 6: 'domingo'}
   daynum = {'lunes':0, 'martes':1, 'miercoles':2, 'miércoles':2, 'jueves':3,
             'viernes':4, 'sabado':5, 'sábado':5, 'domingo':6}
   shifts = {'hoy':0, 'mañana':1, 'pasado':2, 'al otro':3}

   fmt = '%d/%m/%Y-%H:%M'
   try: return dt.datetime.strptime(line, fmt)
   except ValueError:
      pattern = r'([ ^\W\w\d_ ]*) (\S+)'
      match = re.search(pattern, line)
      date,time = match.groups()
      date = date.lower()
      h,m = parse_time(time)
      if date in daynum.keys(): ###############################  Using weekdays
         qday = daynum[date]
         now = dt.datetime.now()
         day = dt.timedelta(days=1)
         wds = []
         for i in range(7):
            d = (now + i*day).weekday()
            if d==qday: break
         date = now + i*day
      else: ##############################################  Using relative days
         shifts = {'hoy':0, 'mañana':1, 'pasado':2, 'pasado mañana':2,
                   'al otro':3}
         delta = dt.timedelta(days=shifts[date.lower()])
         now = dt.datetime.now()
         date = now+delta
      return date.replace(hour=h, minute=m, second=0, microsecond=0)
   except: raise


def locate(date,prop):
   UTCshift = dt.datetime.now()-dt.datetime.utcnow()
   utcdate = date - UTCshift
   now = dt.datetime.utcnow()
   day = dt.timedelta(days=1)
   if   utcdate.date() == now.date(): fol = 'SC2'
   elif utcdate.date() == now.date()+day: fol = 'SC2+1'
   elif utcdate.date() == now.date()+2*day: fol = 'SC4+2'
   elif utcdate.date() == now.date()+3*day: fol = 'SC4+3'
   else: return None,None
   fname  = HOME+'/Documents/RASP/PLOTS/w2/%s/'%(fol)
   fname += utcdate.strftime('%H00')
   #fname += utcdate.strftime('%Y/%m/%d/%H00')
   fname += '_%s.jpg'%(prop)
   return fol,fname


def general(bot,update,job_queue,args,prop):
   """ echo-like service to check system status """
   LG.info('received request: %s'%(update.message.text))
   chatID = update.message.chat_id
   d = ' '.join(args)
   try: date = parser_date(d)
   except:
      txt = 'Sorry, I didn\'t understand\n'
      txt += 'Usage: /fcst %d/%m/%Y-%H:%M\n'
      txt += '       /fcst [hoy/mañana/pasado/al otro] %H\n'
      txt += '       /fcst [hoy/mañana/pasado/al otro] %H:%M\n'
      txt += 'ex: /fcst 18/05/2019-13:00\n'
      txt += '    /fcst mañana 13:00\n'
      txt += '    /fcst al otro 14'
      bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')
      return
   _,f = locate(date, prop)
   if f == None:
      txt = 'Sorry, forecast not available'
      bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')
      return
   prop_names = {'sfcwind':'Surface wind', 'blwind':'BL wind',
                 'bltopwind':'top BL wind', 'cape':'CAPE',
                 'wstar': 'Thermal Height', 'hbl': 'Height of BL Top'}
   txt = prop_names[prop]+' for %s'%(date.strftime('%d/%m/%Y-%H:%M'))
   try:
      f = os.popen("grep %s %s"%(f, f_id_files)).read().strip().split()[-1]
   except: pass
   M = send_picture(bot, chatID, job_queue, f, msg=txt, t=180,delete=True)
   f_ID = M['photo'][-1]['file_id']
   if f[0] == '/':   # means that f is the abs path of the file
      with open(f_id_files,'a') as fw:
         fw.write(str(f)+'   '+str(f_ID)+'\n')
      fw.close()

def techo(bot,update,job_queue,args):
   general(bot,update,job_queue,args,'hbl')

def thermal(bot,update,job_queue,args):
   general(bot,update,job_queue,args,'wstar')

def cape(bot,update,job_queue,args):
   general(bot,update,job_queue,args,'cape')

def fcst(bot,update,job_queue,args):
   general(bot,update,job_queue,args,'sfcwind')

def sfcwind(bot,update,job_queue,args):
   general(bot,update,job_queue,args,'sfcwind')

def blwind(bot,update,job_queue,args):
   general(bot,update,job_queue,args,'blwind')

def bltopwind(bot,update,job_queue,args):
   general(bot,update,job_queue,args,'bltopwind')


def sounding(bot,update,job_queue,args):
   """ echo-like service to check system status """
   LG.info('received request: %s'%(update.message.text))
   chatID = update.message.chat_id
   places = {'arcones': 1, 'bustarviejo': 2, 'cebreros': 3, 'abantos': 4,
             'piedrahita': 5, 'pedro bernardo': 6, 'lillo': 7,
             'fuentemilanos': 8, 'candelario': 10, 'pitolero': 11,
             'pegalajar': 12, 'otivar': 13}
   place = ' '.join(args[:-2])
   index = places[place.lower()]
   date = ' '.join(args[-2:])
   try: date = parser_date(date)
   except:
      txt = 'Sorry, I didn\'t understand\n'
      txt += 'Usage: /sounding {place} %d/%m/%Y-%H:%M\n'
      txt += 'ex: /sounding Arcones 18/05/2019-13:00'
      bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')
      return
   fmt = '%d_%m_%Y_%H_%M'
   txt = "Sounding for *%s* at *%s*"%(place.capitalize(), date.strftime(fmt))
   fol,_ = locate(date,'')
   H = date.strftime('%H%M')
   url_picture = f'http://raspuri.mooo.com/RASP/'
   url_picture += f'{fol}/FCST/sounding{index}.curr.{H}lst.w2.png'
   f_tmp = '/tmp/' + rand_name() + '.png'
   urlretrieve(url_picture, f_tmp)
   send_picture(bot, chatID, job_queue, f_tmp, msg=txt, t=60,delete=True)
   os.system(f'rm {f_tmp}')

def tormentas(bot,update,job_queue,args):
   chatID = update.message.chat_id
   def usage():
      txt = 'Available places:\n'
      txt += ' - Guadarrama, Somosierra, Gredos\n'
      txt += '(case insensitive)\n'
      txt += 'Available dates:\n'
      txt += ' - hoy, mañana, pasado, al otro, al siguiente\n'
      txt += 'Ex: /tormentas gredos mañana\n'
      txt += '      /tormentas Guadarrama al otro\n'
      txt += '      /tormentas somosierra hoy\n'
      M = bot.send_message(chatID, text=txt, parse_mode='Markdown')
   names = {'picos de europa': 'peu1',
            'pirineo navarro': 'nav1',
            'pirineo aragones': 'arn1',
            'pirineo catalan': 'cat1',
            'iberica riojana': 'rio1',
            'sierra de gredos': 'gre1', 'gredos': 'gre1',
            'guadarrama': 'mad2', 'somosierra': 'mad2',
            'iberica aragonesa': 'arn2',
            'sierra nevada': 'nev1'}
   dates = {'hoy':2, 'mañana':3, 'pasado':4, 'al otro':5, 'al siguiente':6}

   if len(args) == 0:
      usage()
      return
   place = args[0].strip().lower()
   place = names[place]
   date = ' '.join(args[1:]).lower()
   w = dates[date]
   url = f'http://www.aemet.es/es/eltiempo/prediccion/montana?w={w}&p={place}'
   txt = str(aemet.parse_parte_aemet(url))
   M = bot.send_message(chatID, text=txt, parse_mode='Markdown')


## Auxiliary ###################################################################
from random import choice
def hola(bot, update):
   """ echo-like service to check system status """
   LG.info('Hola!')
   chatID = update.message.chat_id
   salu2 = ['What\'s up?', 'Oh, hi there!', 'How you doin\'?', 'Hello!']
   txt = choice(salu2)
   M = bot.send_message(chatID, text=txt, parse_mode='Markdown')
