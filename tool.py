#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import common
RP = common.load(fname='config.ini')

# Telegram
import telegram
import telegram.ext
from telegram import ChatAction, ParseMode
# My Libraies
import credentials as CR
import aemet
import admin
from admin import EntryNotFound
# Standard
import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib import gridspec
import string
from urllib.request import urlretrieve
from urllib.error import HTTPError
import datetime as dt
from random import choice
import os
here = os.path.dirname(os.path.realpath(__file__))

# Log
import log_help
import logging
LG = logging.getLogger(__name__)

f_id_files = here+'/files.db'
fmt = '%d/%m/%Y-%H:%M'

fname = 'rasp_var.dict'
var_dict = open(fname,'r').read().strip()
keys,values = [],[]
for l in var_dict.splitlines():
   k,v = l.split(',')
   keys.append(k)
   values.append(v)
prop_names = dict(zip(keys,values))

class PlotDescriptor(object):
   def __init__(self,date_valid,vector,scalar,cover,fname=''):
      """ date_valid has to be a datetime object """
      fmt = '%d/%m/%Y-%H:00'
      self.date_valid = date_valid.strftime(fmt)
      self.vector = str(vector)
      self.scalar = str(scalar)
      self.cover  = str(cover)
      self.fname  = str(fname)
   def __str__(self):
      msg =  f'Date  : {self.date_valid}\n'
      msg += f'Vector: {self.vector}\n'
      msg += f'Scalar: {self.scalar}\n'
      msg += f'File: {self.fname}'
      return msg


def call_delete(context: telegram.ext.CallbackContext):
   """
    context.job.context should carry the chatID and the msgID
   """
   chatID, msgID = context.job.context
   m = context.bot.delete_message(chatID, msgID)


@log_help.timer(LG)
def send_media(bot,chatID,job_queue, P, caption='', t_del=None, t_renew=600,
                                                dis_notif=False, recycle=False,
                                                db_file='RaspBot.db'):
   """
   media_file: file to be sent
   t_renew: if file was registered in the database longer than t_renew seconds,
            send the file again and replace the entry
   recycle: Boolean. check DB for previous send
   """
   media_file = P.fname   #XXX report missing file??
   if media_file[-4:] in ['.jpg', '.png']:
      send_func = bot.send_photo
      media = open(media_file,'rb')
      Action = ChatAction.UPLOAD_PHOTO
   elif media_file[-4:] in ['.mp4', '.gif']:
      send_func = bot.send_video
      media = open(media_file,'rb')
      Action = ChatAction.UPLOAD_VIDEO

   conn,c = admin.connect(db_file)
   now = dt.datetime.now()
   skip = False
   if recycle:
      LG.debug(f'Checking DB {db_file}')
      try:
         # admin.show_all(conn)
         ff = admin.get_file(conn, P.date_valid, P.vector, P.scalar, P.cover)
         LG.debug('Entry found')
         date = dt.datetime.strptime(ff[0][0],fmt)
         f_id = ff[0][-1]
         if (now-date).total_seconds() < t_renew:
            LG.debug(f'Re-using {media_file}, previously sent')
            media = f_id
            skip = True
         else:
            LG.debug(f'{media_file} is too old. Delete entry and send again')
            admin.remove_file(conn,f_id)
      except EntryNotFound: pass
   else: pass
   bot.send_chat_action(chat_id=chatID, action=Action)
   if Action == ChatAction.UPLOAD_VIDEO and not isinstance(media,str):
      txt =  'Nadie ha pedido esto aún, puede tardar algún minutillo en llegar'
      txt += ', disculpa las molestias.'
      bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
   LG.debug(f'Sending {media}')
   M = send_func(chatID, media, caption=caption,
                                timeout=300, disable_notification=dis_notif,
                                parse_mode=ParseMode.MARKDOWN)
   admin.user_usage(conn,chatID,1)
   LG.info(f'File sent to chat {chatID}')
   try: file_id = M['photo'][-1]['file_id']
   except IndexError: file_id = M['video']['file_id']
   if not skip:
      admin.insert_file(conn, now.strftime(fmt), P.date_valid, P.vector,
                              P.scalar, P.cover,file_id)
      # admin.insert_file(conn, P.now.year,now.month,now.day,now.hour,now.minute,
      #                   media_file, file_id)
   if t_del != None:
      msgID = M.message_id
      job_queue.run_once(call_delete,t_del, context=(chatID, msgID))


def rand_name(pwdSize=8):
   """ Generates a random string of letters and digits with pwdSize length """
   ## all possible letters and numbers
   chars = string.ascii_letters + string.digits
   return ''.join((choice(chars)) for x in range(pwdSize))

#def parse_time(time):
#   try:
#      pattern = r'(\S+):(\S+)'
#      match = re.search(pattern, time)
#      h,m = (match.groups())
#      m = 0
#   except AttributeError:
#      h = time
#      m = 0
#   return int(h), int(m)
#
#
#def parser_date(line):
#   numday = {0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
#             4: 'viernes', 5: 'sábado', 6: 'domingo'}
#   daynum = {'lunes':0, 'martes':1, 'miercoles':2, 'miércoles':2, 'jueves':3,
#             'viernes':4, 'sabado':5, 'sábado':5, 'domingo':6}
#   shifts = {'hoy':0, 'mañana':1, 'pasado':2, 'pasado mañana':2, 'al otro':3}
#
#   notime = False
#   try: return dt.datetime.strptime(line, fmt)
#   except ValueError:
#      try:
#         pattern = r'([ ^\W\w\d_ ]*) (\S+)'
#         match = re.search(pattern, line)
#         date,time = match.groups()
#      except AttributeError:
#         pattern = r'([ ^\W\w\d_ ]*)'
#         match = re.search(pattern, line)
#         date = match.groups()[0]
#         time = '0:0'
#         notime = True
#      date = date.lower()
#      h,m = parse_time(time)
#      if date in daynum.keys(): ###############################  Using weekdays
#         qday = daynum[date]
#         now = dt.datetime.now()
#         day = dt.timedelta(days=1)
#         wds = []
#         for i in range(7):
#            d = (now + i*day).weekday()
#            if d==qday: break
#         date = now + i*day
#      else: ##############################################  Using relative days
#         delta = dt.timedelta(days=shifts[date.lower()])
#         now = dt.datetime.now()
#         date = now+delta
#      if notime: return date.date()
#      else: return date.replace(hour=h, minute=m, second=0, microsecond=0)
#   except: raise

def decide_image(date,scalar,vector,cover,bot,chatID,job_queue,dpi=65):
   """
   date here is local
   """
   dateUTC = date - get_utc_shift()
   dom='w2'
   sc = get_sc(date)   # XXX should it be UTC????
   root_fol = RP.fol_plots    
   if date.time()==dt.time(0,0):
      f_tmp = f'{root_fol}/{dom}/{sc}/{scalar}.mp4'
   else:
      f_tmp = build_image(date,scalar,vector,cover,dpi=dpi)
   txt = f"{prop_names[scalar]} para el {date.strftime('%d/%m/%Y-%H:00')}"
   P =  PlotDescriptor(dateUTC,vector,scalar,cover,fname=f_tmp)
   send_media(bot,chatID,job_queue, P, caption=txt,
                                       t_del=5*60, t_renew=6*60*60,
                                       dis_notif=False,
                                       recycle=False)

def build_image(date,scalar,vector,cover,dpi=65):
   """
   Date comes in local time. After the first line it should be converted to UTC
   """
   dateUTC = date - get_utc_shift()
   dom='w2'
   sc = get_sc(dateUTC)   # XXX should it be UTC????
   root_fol = RP.fol_plots
   fol = f'{root_fol}/{dom}/{sc}'
   grids_fol = RP.fol_grids
   f_tmp = '/tmp/' + rand_name() + '.png'
   f_tmp1 = '/tmp/' + rand_name() + '.png'
   P =  PlotDescriptor(dateUTC,vector,scalar,cover,fname=f_tmp)
   props = {'sfcwind':'Viento Superficie', 'blwind':'Viento Promedio',
            'bltopwind':'Viento Altura', 'hglider':'Techo (azul)',
            'wstar':'Térmica', 'zsfclcl':'Base nube', 'zblcl':'Cielo cubierto',
            'cape':'CAPE', 'wblmaxmin':'Convergencias' }
   hora = dateUTC.strftime('%H00')
   title = f"{date.strftime('%d/%m/%Y-%H:%M')} {props[scalar]}"
   terrain = f'{fol}/terrain.png'
   rivers = f'{fol}/rivers.png'
   ccaa = f'{fol}/ccaa.png'
   takeoffs = f'{fol}/takeoffs.png'
   bar = f'{root_fol}/{scalar}_light.png'
   if vector != 'none': vector = f'{fol}/{hora}_{vector}_vec.png'
   else: vector = None
   scalar = f'{fol}/{hora}_{scalar}.png'
   LG.debug(vector)
   LG.debug(scalar)
   lats = f'{grids_fol}/{dom}/{sc}/lats.npy'
   lons = f'{grids_fol}/{dom}/{sc}/lons.npy'
   lats = np.load(lats)
   lons = np.load(lons)
   d_x = np.max(lons)-np.min(lons)
   d_y = np.max(lats)-np.min(lats)
   dy,dx = lons.shape
   # aspects = {'SC2':2.25, 'SC2+1':2.25, 'SC4+2':1.3, 'SC4+3':1.3}
   aspects = {'w2':{'SC2':2.25, 'SC2+1':2.25, 'SC4+2':1.3, 'SC4+3':1.3},
              'd2':{'SC2':1.9, 'SC2+1':1.9, 'SC4+2':1.9, 'SC4+3':1.9}}
   aspect = aspects[dom][sc]*d_y/d_x
   aspect = 1.
   # Read Images
   terrain = mpimg.imread(terrain)
   rivers = mpimg.imread(rivers)
   ccaa = mpimg.imread(ccaa)
   takeoffs = mpimg.imread(takeoffs)
   if vector != None: img_vector = mpimg.imread(vector)
   img_scalar = mpimg.imread(scalar)
   bar = mpimg.imread(bar)
   # Output Images
   fig = plt.figure()
   gs = gridspec.GridSpec(2, 1, height_ratios=[7.2,1])
   fig.subplots_adjust(wspace=0.,hspace=0.)
   ax1 = plt.subplot(gs[0,0])
   ax2 = plt.subplot(gs[1,0])
   ax1.imshow(terrain,aspect=aspect,interpolation='lanczos',zorder=0)
   ax1.imshow(rivers,aspect=aspect,interpolation='lanczos',zorder=0)
   ax1.imshow(ccaa,aspect=aspect,interpolation='lanczos',zorder=20)
   ax1.imshow(takeoffs,aspect=aspect,interpolation='lanczos',zorder=20)
   if vector != None:
      ax1.imshow(img_vector, aspect=aspect, interpolation='lanczos',
                             zorder=11, alpha=0.75)
   ax1.imshow(img_scalar, aspect=aspect, interpolation='lanczos',
                          zorder=10, alpha=0.5)
   ax1.set_xticks([])
   ax1.set_yticks([])
   ax1.set_title(title)
   ax1.axis('off')
   ax2.imshow(bar)
   ax2.set_xticks([])
   ax2.set_yticks([])
   ax2.axis('off')
   fig.tight_layout()
   fig.savefig(f_tmp)
   
   os.system(f'convert {f_tmp} -trim {f_tmp1}')
   os.system(f'mv {f_tmp1} {f_tmp}')
   return f_tmp


def send_sounding(place,date,bot,chatID,job_queue, t_del=5*60,
                                                   t_renew=6*60*60,
                                                   dis_notif=False):
   dateUTC = date - get_utc_shift()
   places = {'arcones': 1, 'bustarviejo': 2, 'cebreros': 3, 'abantos': 4,
             'piedrahita': 5, 'pedro bernardo': 6, 'lillo': 7,
             'fuentemilanos': 8, 'candelario': 10, 'pitolero': 11,
             'pegalajar': 12, 'otivar': 13}
   fol = get_sc(date)
   index = places[place]
   H = date.strftime('%H%M')
   url_picture = 'http://raspuri.mooo.com/RASP/'
   url_picture += f'{fol}/FCST/sounding{index}.curr.{H}lst.w2.png'
   LG.debug(url_picture)
   f_tmp = '/tmp/' + rand_name() + '.png'
   urlretrieve(url_picture, f_tmp)
   T = aemet.get_temp(place,date)
   fmt = '%d/%m/%Y-%H:%M'
   txt = f"Sounding for _{place.capitalize()}_ at {date.strftime(fmt)}"
   if T != None:
      txt += f'\nExpected temperature: *{T}°C*'
   ##tool.send_media(update,context, f_tmp, msg=txt, t=180,delete=True)
   P =  PlotDescriptor(dateUTC,None,None,None,fname=f_tmp)
   # bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_PHOTO)
   send_media(bot,chatID,job_queue, P, caption=txt,
                                         t_del=5*60, t_renew=6*60*60,
                                         dis_notif=False,recycle=False)
   os.system(f'rm {f_tmp}')
   return

def send_rain(date,bot,chatID,job_queue, t_del=5*60,t_renew=6*60*60,
                                                   dis_notif=False):
   """
   Send Aemet's forecast for rain [around Madrid]
   """
   dateUTC = date - get_utc_shift()
   f_tmp = '/tmp/' + rand_name() + '.png'
   try: urlretrieve(aemet.rain(date), f_tmp)
   except HTTPError:
      txt = 'Lo siento, el pronóstico que has pedido no está disponible\n'
      txt += 'Puedes comprobar las horas disponibles aquí:\n'
      txt += 'https://www.aemet.es/es/eltiempo/prediccion/modelosnumericos/'
      txt += 'harmonie_arome_ccaa?opc2=mad&opc3=pr'
      bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
      return
   P =  PlotDescriptor(dateUTC,None,None,None,fname=f_tmp)
   # bot.send_chat_action(chat_id=chatID, action=ChatAction.UPLOAD_PHOTO)
   txt = 'Lluvia acumulada en 1 hora, sacada de Aemet:\n'
   txt += 'https://www.aemet.es/es/eltiempo/prediccion/modelosnumericos/'
   txt += 'harmonie_arome_ccaa?opc2=mad&opc3=pr'
   send_media(bot,chatID,job_queue, P, caption=txt,
                                         t_del=5*60, t_renew=6*60*60,
                                         dis_notif=False,recycle=False)
   os.system(f'rm {f_tmp}')


def get_utc_shift():
   UTCshift = dt.datetime.now()-dt.datetime.utcnow()
   return dt.timedelta(hours = round(UTCshift.total_seconds()/3600))

def get_sc(date):
   ## XXX should everything be in UTC?
   # UTCshift = dt.datetime.now()-dt.datetime.utcnow()
   # utcdate = date - UTCshift
   # now = dt.datetime.utcnow()
   now = dt.datetime.now()
   day = dt.timedelta(days=1)
   if   date.date() == now.date(): return 'SC2'
   elif date.date() == now.date()+day: return 'SC2+1'
   elif date.date() == now.date()+2*day: return 'SC4+2'
   elif date.date() == now.date()+3*day: return 'SC4+3'
   else: return None

#def locate(date,prop):
#   # UTCshift = dt.datetime.now()-dt.datetime.utcnow()
#   # utcdate = date - UTCshift
#   # now = dt.datetime.utcnow()
#   fname  = HOME+'/Documents/RASP/PLOTS/w2/'
#   # day = dt.timedelta(days=1)
#   # build_image(date,prop)
#   if isinstance(utcdate, dt.datetime):
#      fol = get_sc(date)
#      if fol == None: return None,None
#      fname += fol + utcdate.strftime('/%H00')
#      fname += '_%s.png'%(prop)
#      return fol,fname
#   else:
#      if   utcdate == now.date(): fol = 'SC2'
#      elif utcdate == now.date()+day: fol = 'SC2+1'
#      elif utcdate == now.date()+2*day: fol = 'SC4+2'
#      elif utcdate == now.date()+3*day: fol = 'SC4+3'
#      fname += fol+'/'+prop+'.mp4'
#      return fol,fname
#
#
#def general(update,context,prop): #(bot,update,job_queue,args,prop):
#   """ echo-like service to check system status """
#   LG.info('received request: %s'%(update.message.text))
#   #conn,c = admin.connect('files.db')
#   try: chatID = update['message']['chat']['id']
#   except TypeError: chatID = update['callback_query']['message']['chat']['id']
#   bot = context.bot
#   job_queue = context.job_queue
#   d = ' '.join(context.args)
#   try: date = parser_date(d)
#   except:
#      txt = 'Sorry, I didn\'t understand\n'
#      txt += 'Usage: /fcst %d/%m/%Y-%H:%M\n'
#      txt += '       /fcst [hoy/mañana/pasado/al otro] %H\n'
#      txt += '       /fcst [hoy/mañana/pasado/al otro] %H:%M\n'
#      txt += 'ex: /fcst 18/05/2019-13:00\n'
#      txt += '    /fcst mañana 13:00\n'
#      txt += '    /fcst al otro 14'
#      bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
#      return
#   fol,f = locate(date, prop)
#   if f == None:
#      txt = 'Sorry, forecast not available'
#      bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
#      return
#   prop_names = {'sfcwind':'Surface wind', 'blwind':'BL wind',
#                 'bltopwind':'top BL wind', 'cape':'CAPE',
#                 'wstar': 'Thermal Height', 'hbl': 'Height of BL Top',
#                 'blcloudpct': '1h Accumulated Rain'}
#   if f[-4:] == '.mp4':
#      txt = prop_names[prop]+' for %s'%(date.strftime('%d/%m/%Y'))
#   else:
#      txt = prop_names[prop]+' for %s'%(date.strftime('%d/%m/%Y-%H:%M'))
#   RP = common.load(fname='config.ini')
#   # send_media(bot,chatID,job_queue, f, caption=txt,
#   #                                     t_del= RP.t_del, t_renew=RP.t_renew,
#   #                                     dis_notif=False)
#
#
#def techo(update, context):     general(update,context,'hbl')
#
#def thermal(update, context):   general(update,context,'wstar')
#
#def cape(update, context):      general(update,context,'cape')
#
#def sfcwind(update, context):   general(update,context,'sfcwind')
#
#def blwind(update, context):    general(update,context,'blwind')
#
#def bltopwind(update, context): general(update,context,'bltopwind')
#
#def blcloud(update, context):   general(update,context,'blcloudpct')
#
#
#def tormentas(update, context):  #(bot,update,job_queue,args):
#   try: chatID = update['message']['chat']['id']
#   except TypeError: chatID = update['callback_query']['message']['chat']['id']
#   def usage():
#      txt = 'Available places:\n'
#      txt += ' - Guadarrama, Somosierra, Gredos\n'
#      txt += '(case insensitive)\n'
#      txt += 'Available dates:\n'
#      txt += ' - hoy, mañana, pasado, al otro, al siguiente\n'
#      txt += 'Ex: /tormentas gredos mañana\n'
#      txt += '      /tormentas Guadarrama al otro\n'
#      txt += '      /tormentas somosierra hoy\n'
#      M = context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
#   names = {'picos de europa': 'peu1',
#            'pirineo navarro': 'nav1',
#            'pirineo aragones': 'arn1',
#            'pirineo catalan': 'cat1',
#            'iberica riojana': 'rio1',
#            'sierra de gredos': 'gre1', 'gredos': 'gre1',
#            'guadarrama': 'mad2', 'somosierra': 'mad2',
#            'iberica aragonesa': 'arn2',
#            'sierra nevada': 'nev1'}
#   dates = {'hoy':2, 'mañana':3, 'pasado':4, 'al otro':5, 'al siguiente':6}
#
#   if len(context.args) == 0:
#      usage()
#      return
#   place = context.args[0].strip().lower()
#   place = names[place]
#   date = ' '.join(context.args[1:]).lower()
#   w = dates[date]
#   url = f'http://www.aemet.es/es/eltiempo/prediccion/montana?w={w}&p={place}'
#   txt = '`'+str(aemet.parse_parte_aemet(url))+'`\n'
#   txt += f'Taken from {url}'
#   M = context.bot.send_message(chatID, text=txt,
#                                disable_web_page_preview=True,
#                                parse_mode=ParseMode.MARKDOWN)
#
#
## Auxiliary ###################################################################
def hola(update, context):
   """ echo-like service to check system status """
   LG.info('Hola!')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   salu2 = ['What\'s up?', 'Oh, hi there!', 'How you doin\'?', 'Hello!']
   txt = choice(salu2)
   M = context.bot.send_message(chatID, text=txt, 
                                parse_mode=ParseMode.MARKDOWN)

def help_txt():
   txt =  f"```/sfcwind``` - Viento en superficie\n"
   txt += f"```/bltopwind``` - Viento en el tope de la capa convectiva\n"
   txt += f"```/blwind``` - Viento promedio de toda la capa convectiva\n"
   txt += f"```/techo``` - Altura máxima de las térmicas (en días de térmica azul)\n"
   txt += f"```/termicas``` - Potencia máxima de las térmicas\n"
   txt += f"```/convergencias``` - Velocidad vertical máxima del viento (ignorando térmicas)\n"
   txt += f"```/sondeo``` - Curva de estado\n"
   txt += f"```/lluvia``` - Lluvia acumulada en 1 hora (sacada de Aemet)\n"
   txt += f"```/map``` - Mapa personalizado, combinando el flujo de viento deseado con cualquier otra propiedad\n"
   return txt.strip()

def myhelp(update, context):
   """ echo-like service to check system status """
   LG.info('Help')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   txt = help_txt()
   M = context.bot.send_message(chatID, text=txt, 
                                parse_mode=ParseMode.MARKDOWN)

@CR.restricted(0)
def log(update, context):
   LG.info('Log')
   def tail(fname, n=10, bs=1024):
      with open(fname) as f:
         f.seek(0,2)
         l = 1-f.read(1).count('\n')
         B = f.tell()
         while n >= l and B > 0:
            block = min(bs, B)
            B -= block
            f.seek(B, 0)
            l += f.read(block).count('\n')
         f.seek(B, 0)
         l = min(l,n)
         lines = f.readlines()[-l:]
      return [l.strip() for l in lines]
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   txt = '\n'.join(tail(RP.log,3))
   txt = f'```\n{txt}\n```'
   M = context.bot.send_message(chatID, text=txt, 
                                parse_mode=ParseMode.MARKDOWN)
