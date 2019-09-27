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

def send_video(update,context, vid, msg='',
               t=60,delete=True,dis_notif=False,warn_wait=True):
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   func = context.bot.send_video
   if vid[:4] == 'http': video = vid
   else:
      try:
         video = open(vid, 'rb')  # TODO raise and report if file not found
         if warn_wait:
            txt = 'This usually takes a few seconds... be patient'
            M1 = context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
      except:
         video = vid
         func = context.bot.send_animation
   context.bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_VIDEO)
   M = func(chatID, video, caption=msg,
                              timeout=300, disable_notification=dis_notif,
                              parse_mode=ParseMode.MARKDOWN)
   t=30
   if delete:
      tdel = dt.datetime.now()+dt.timedelta(seconds=t)
      LG.debug('vid %s to be deleted at %s'%(vid,tdel))
      msgID = M.message_id
      context.job_queue.run_once(call_delete,t, context=(chatID, msgID))
   return M


def send_picture(update,context, pic, msg='',t=60,delete=True,dis_notif=False):
   """
    Send a picture and, optionally, remove it locally/remotely (rm/delete)
    pic = photo to send
    msg = caption of the picture
    t = time to wait to delete the remote picture
    delete = remove remote file t seconds after sending
    dis_notif = Disable sound notification
   """
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   LG.info('Sending picture: %s'%(pic))
   if pic[:4] == 'http': photo = pic
   else:
      try: photo = open(pic, 'rb')  # TODO raise and report if file not found
      except: photo = pic
   context.bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_PHOTO)
   M = context.bot.send_photo(chatID, photo, caption=msg,
                              timeout=300, disable_notification=dis_notif,
                              parse_mode=ParseMode.MARKDOWN)
   t=30
   if delete:
      tdel = dt.datetime.now()+dt.timedelta(seconds=t)
      LG.debug('pic %s to be deleted at %s'%(pic,tdel))
      msgID = M.message_id
      context.job_queue.run_once(call_delete,t, context=(chatID, msgID))
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
   conn,c = admin.connect('files.db')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
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
      context.bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
      return
   fol,f = locate(date, prop)
   if f == None:
      txt = 'Sorry, forecast not available'
      context.bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
      return
   prop_names = {'sfcwind':'Surface wind', 'blwind':'BL wind',
                 'bltopwind':'top BL wind', 'cape':'CAPE',
                 'wstar': 'Thermal Height', 'hbl': 'Height of BL Top'}
   txt = prop_names[prop]+' for %s'%(date.strftime('%d/%m/%Y-%H:%M'))
   if f[-4:] == '.mp4': send_func = send_video
   elif f[-4:] in ['.png','.jpg']: send_func = send_picture
   ff = admin.get_file(conn,c, fol, date.strftime('%H%M'), prop,'files')
   if len(ff) == 1: f, =ff[0]
   M = send_func(update,context, f, msg=txt, t=180,delete=True)
   try: f_ID = M['photo'][-1]['file_id']
   except: f_ID = M['animation']['file_id']
   if f[0] == '/':   # means that f is the abs path of the file
      now = dt.datetime.now()
      admin.insert_file(conn,c, now.year, now.month, now.day, now.hour,
                        now.minute, 'SC2',date.strftime('%H%M'), prop,
                        str(f_ID),'files')


def techo(update, context):     general(update,context,'hbl')

def thermal(update, context):   general(update,context,'wstar')

def cape(update, context):      general(update,context,'cape')

def sfcwind(update, context):   general(update,context,'sfcwind')

def blwind(update, context):    general(update,context,'blwind')

def bltopwind(update, context): general(update,context,'bltopwind')


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
