#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from telegram import ChatAction, ParseMode
import telegram
import string
from urllib.request import urlretrieve
import datetime as dt
import aemet
import re
import admin
from admin import EntryNotFound
import logging
import os
here = os.path.dirname(os.path.realpath(__file__))
HOME = os.getenv('HOME')
LG = logging.getLogger(__name__)
#f_id_files = here+'/pics_ids.txt'
f_id_files = here+'/files.db'

def call_delete(context: telegram.ext.CallbackContext):
   """
    context.job.context should carry the chatID and the msgID
   """
   chatID, msgID = context.job.context
   m = context.bot.delete_message(chatID, msgID)


def send_media(bot,chatID,job_queue, media_file, caption='',
                                                 t_del=None, t_renew=600,
                                                 dis_notif=False):
   """
   media_file: file to be sent
   t_renew: if file was registered in the database longer than t_renew seconds,
            send the file again and replace the entry
   """
   if media_file[-4:] in ['.jpg', '.png']:
      send_func = bot.send_photo
      media = open(media_file,'rb')
      Action = ChatAction.UPLOAD_PHOTO
   elif media_file[-4:] in ['.mp4', '.gif']:
      send_func = bot.send_video
      media = open(media_file,'rb')
      Action = ChatAction.UPLOAD_VIDEO

   conn,c = admin.connect('RaspBot.db')
   now = dt.datetime.now()
   skip = False
   try:
      ff = admin.get_file(conn, 'fname', media_file)
      date = dt.datetime(*list(map(int,ff[0][:5])))
      if (now-date).total_seconds() < t_renew:
         media = ff[0][-1]
         if send_func == bot.send_video:
            send_func = bot.send_animation
         skip = True
      else:
         LG.info(f'{media_file} is too old, deleting entry ')
         admin.remove_file(conn,'fname', media_file)
   except EntryNotFound: pass
   bot.send_chat_action(chat_id=chatID, action=Action)
   M = send_func(chatID, media, caption=caption,
                                timeout=300, disable_notification=dis_notif,
                                parse_mode=ParseMode.MARKDOWN)
   try: file_id = M['photo'][-1]['file_id']
   except IndexError: file_id = M['animation']['file_id']
   if not skip:
      admin.insert_file(conn, now.year,now.month,now.day,now.hour,now.minute,
                        media_file, file_id)
   if t_del != None:
      msgID = M.message_id
      job_queue.run_once(call_delete,t_del, context=(chatID, msgID))


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
   shifts = {'hoy':0, 'mañana':1, 'pasado':2, 'pasado mañana':2, 'al otro':3}

   fmt = '%d/%m/%Y-%H:%M'
   notime = False
   try: return dt.datetime.strptime(line, fmt)
   except ValueError:
      try:
         pattern = r'([ ^\W\w\d_ ]*) (\S+)'
         match = re.search(pattern, line)
         date,time = match.groups()
      except AttributeError:
         pattern = r'([ ^\W\w\d_ ]*)'
         match = re.search(pattern, line)
         date = match.groups()[0]
         time = '0:0'
         notime = True
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
         delta = dt.timedelta(days=shifts[date.lower()])
         now = dt.datetime.now()
         date = now+delta
      if notime: return date.date()
      else: return date.replace(hour=h, minute=m, second=0, microsecond=0)
   except: raise


def locate(date,prop):
   UTCshift = dt.datetime.now()-dt.datetime.utcnow()
   utcdate = date - UTCshift
   now = dt.datetime.utcnow()
   fname  = HOME+'/Documents/RASP/PLOTS/w2/'
   day = dt.timedelta(days=1)
   if isinstance(utcdate, dt.datetime):
      if   utcdate.date() == now.date(): fol = 'SC2'
      elif utcdate.date() == now.date()+day: fol = 'SC2+1'
      elif utcdate.date() == now.date()+2*day: fol = 'SC4+2'
      elif utcdate.date() == now.date()+3*day: fol = 'SC4+3'
      else: return None,None
      fname += fol + utcdate.strftime('/%H00')
      fname += '_%s.jpg'%(prop)
      return fol,fname
   else:
      if   utcdate == now.date(): fol = 'SC2'
      elif utcdate == now.date()+day: fol = 'SC2+1'
      elif utcdate == now.date()+2*day: fol = 'SC4+2'
      elif utcdate == now.date()+3*day: fol = 'SC4+3'
      fname += fol+'/'+prop+'.mp4'
      return fol,fname


def general(update,context,prop): #(bot,update,job_queue,args,prop):
   """ echo-like service to check system status """
   LG.info('received request: %s'%(update.message.text))
   #conn,c = admin.connect('files.db')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   bot = context.bot
   job_queue = context.job_queue
   d = ' '.join(context.args)
   try: date = parser_date(d)
   except:
      txt = 'Sorry, I didn\'t understand\n'
      txt += 'Usage: /fcst %d/%m/%Y-%H:%M\n'
      txt += '       /fcst [hoy/mañana/pasado/al otro] %H\n'
      txt += '       /fcst [hoy/mañana/pasado/al otro] %H:%M\n'
      txt += 'ex: /fcst 18/05/2019-13:00\n'
      txt += '    /fcst mañana 13:00\n'
      txt += '    /fcst al otro 14'
      bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
      return
   fol,f = locate(date, prop)
   if f == None:
      txt = 'Sorry, forecast not available'
      bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
      return
   prop_names = {'sfcwind':'Surface wind', 'blwind':'BL wind',
                 'bltopwind':'top BL wind', 'cape':'CAPE',
                 'wstar': 'Thermal Height', 'hbl': 'Height of BL Top',
                 'blcloudpct': '1h Accumulated Rain'}
   if f[-4:] == '.mp4':
      txt = prop_names[prop]+' for %s'%(date.strftime('%d/%m/%Y'))
   else:
      txt = prop_names[prop]+' for %s'%(date.strftime('%d/%m/%Y-%H:%M'))
   send_media(bot,chatID,job_queue, f, caption=txt,
                                       t_del=5*60, t_renew=6*24*24,
                                       dis_notif=False)


def techo(update, context):     general(update,context,'hbl')

def thermal(update, context):   general(update,context,'wstar')

def cape(update, context):      general(update,context,'cape')

def sfcwind(update, context):   general(update,context,'sfcwind')

def blwind(update, context):    general(update,context,'blwind')

def bltopwind(update, context): general(update,context,'bltopwind')

def blcloud(update, context):   general(update,context,'blcloudpct')


def tormentas(update, context):  #(bot,update,job_queue,args):
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   def usage():
      txt = 'Available places:\n'
      txt += ' - Guadarrama, Somosierra, Gredos\n'
      txt += '(case insensitive)\n'
      txt += 'Available dates:\n'
      txt += ' - hoy, mañana, pasado, al otro, al siguiente\n'
      txt += 'Ex: /tormentas gredos mañana\n'
      txt += '      /tormentas Guadarrama al otro\n'
      txt += '      /tormentas somosierra hoy\n'
      M = context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
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

   if len(context.args) == 0:
      usage()
      return
   place = context.args[0].strip().lower()
   place = names[place]
   date = ' '.join(context.args[1:]).lower()
   w = dates[date]
   url = f'http://www.aemet.es/es/eltiempo/prediccion/montana?w={w}&p={place}'
   txt = '`'+str(aemet.parse_parte_aemet(url))+'`\n'
   txt += f'Taken from {url}'
   M = context.bot.send_message(chatID, text=txt,
                                disable_web_page_preview=True,
                                parse_mode=ParseMode.MARKDOWN)


## Auxiliary ###################################################################
from random import choice
#def hola(bot, update):
def hola(update, context):
   """ echo-like service to check system status """
   LG.info('Hola!')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   salu2 = ['What\'s up?', 'Oh, hi there!', 'How you doin\'?', 'Hello!']
   txt = choice(salu2)
   M = context.bot.send_message(chatID, text=txt, 
                                parse_mode=ParseMode.MARKDOWN)
