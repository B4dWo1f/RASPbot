#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import common
import credentials as CR
RP = common.load(fname='config.ini')
MB = CR.get_credentials(RP.token_file)
from common import command_callback, prop_names

# Telegram
import telegram
import telegram.ext
from telegram import ChatAction, ParseMode
# My Libraies
import aemet
import admin
from admin import EntryNotFound
# Standard
import os
import numpy as np
import matplotlib as mpl
if os.getenv('RUN_BY_CRON'): mpl.use('Agg')
import matplotlib.pyplot as plt
try: plt.style.use('mystyle')
except: pass
import matplotlib.image as mpimg
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


# default_args = t_del=5*60, t_renew=6*60*60, dis_notif=False


class PlotDescriptor(object):
   def __init__(self,date_valid,vector,scalar,cover,fname=''):
      """ date_valid has to be a datetime object """
      fmt = '%d/%m/%Y-%H:00'
      self.date_valid = date_valid.strftime(fmt)   # XXX Local time
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
def send_media(bot,chatID,job_queue, P, userID, caption='',
                                                t_del=None, t_renew=600,
                                                dis_notif=False, recycle=False,
                                                db_file='RaspBot.db',
                                                rm=False,
                                                disable_web_page_preview=None):
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
   #now = dt.datetime.now()
   #skip = False
   #if recycle:
   #   LG.debug(f'Checking DB {db_file}')
   #   try:
   #      # admin.show_all(conn)
   #      ff = admin.get_file(conn, P.date_valid, P.vector, P.scalar, P.cover)
   #      LG.debug('Entry found')
   #      date = dt.datetime.strptime(ff[0][0],fmt)
   #      f_id = ff[0][-1]
   #      if (now-date).total_seconds() < t_renew:
   #         LG.debug(f'Re-using {media_file}, previously sent')
   #         media = f_id
   #         skip = True
   #      else:
   #         LG.debug(f'{media_file} is too old. Delete entry and send again')
   #         admin.remove_file(conn,f_id)
   #   except EntryNotFound: pass
   #else: pass
   bot.send_chat_action(chat_id=chatID, action=Action)
   LG.debug(f'Sending {media}')
   M = send_func(chatID, media, caption=caption,
                                timeout=300, disable_notification=dis_notif,
                                parse_mode=ParseMode.MARKDOWN)
   LG.info(f'File sent to chat {chatID}')
   try: file_id = M['photo'][-1]['file_id']
   except IndexError: file_id = M['video']['file_id']
   try: admin.user_usage(conn,chatID,1)
   except admin.EntryNotFound:
      warn_txt = f'Unregistered user: {chatID}'
      M = bot.send_message(chat_id=MB.me, text=warn_txt,
                           parse_mode=ParseMode.MARKDOWN)
      warn_txt = 'Perdona, no te tengo registrado,'
      warn_txt += 'por favor usa el comando /start y vuelve a intentarlo'
      bot.send_message(chatID, text=warn_txt, parse_mode=ParseMode.MARKDOWN)
   #if not skip:
   #   admin.insert_file(conn, now.strftime(fmt), P.date_valid, P.vector,
   #                           P.scalar, P.cover,file_id)
   #   # admin.insert_file(conn, P.now.year,now.month,now.day,now.hour,now.minute,
   #   #                   media_file, file_id)
   if t_del != None:
      msgID = M.message_id
      job_queue.run_once(call_delete,t_del, context=(chatID, msgID))
   if rm: os.system(f'rm {media_file}')


def rand_name(pwdSize=8):
   """ Generates a random string of letters and digits with pwdSize length """
   ## all possible letters and numbers
   chars = string.ascii_letters + string.digits
   return ''.join((choice(chars)) for x in range(pwdSize))


def decide_image(date,scalar,vector,cover,bot,chatID,job_queue,userID,dpi=65):
   """
   date here is local
   """
   LG.info(f'Decide_image: {date}, {scalar}, {vector}')
   dom='w2'
   # Order is important!! datetime objects are date objects as well
   if isinstance(date,dt.datetime):
      LG.debug(f'Preparing picture for {date}, {scalar}, {vector}, {cover}')
      txt = 'Preparando el mapa, dame un segundo...'
      M = bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
      f_tmp, valid_date = build_image(date,scalar,vector,cover,dpi=dpi)
      txt = '...acabé. Empiezo el envío (puede tardar unos segundos en llegar)'
      bot.edit_message_text(chat_id=chatID, message_id=M['message_id'],
                            text=txt, parse_mode=ParseMode.MARKDOWN)
      rm = True
      txt = f"{prop_names[scalar]} para el "
      txt += f"{valid_date.strftime('%d/%m/%Y-%H:00')}\n"
      txt += 'más info en: http://meteonube.hopto.org'
      P =  PlotDescriptor(date,vector,scalar,cover,fname=f_tmp)
   elif isinstance(date,dt.date):
      LG.debug(f'Preparing video for {date}, {scalar}, {vector}, {cover}')
      root_fol = RP.fol_plots    
      sc = get_sc(date)   # XXX should it be UTC????
      f_tmp = f'{root_fol}/{dom}/{sc}/{scalar}.mp4'
      rm = False
      txt = f"{prop_names[scalar]} para el {date.strftime('%d/%m/%Y')}\n"
      txt += 'más info en: http://meteonube.hopto.org'
      P =  PlotDescriptor(date,vector,scalar,cover,fname=f_tmp)
   else: LG.critical(f'Error in decide_image with time. Recived: {date}')
   send_media(bot,chatID,job_queue, P, userID, caption=txt,
                                       t_del=RP.t_del,  #5*60,
                                       t_renew=RP.t_renew,  #6*60*60,
                                       dis_notif=False,
                                       recycle=False,rm=rm)

def build_image(date,scalar,vector,cover,dpi=65):
   """
   Date comes in local time. After the first line it should be converted to UTC
   """
   dateUTC = date - get_utc_shift()
   dom='w2'
   sc = get_sc(dateUTC.date())   # It has to be UTC because the data files
                                 # are stored using utc time
   root_fol = RP.fol_plots
   fol = f'{root_fol}/{dom}/{sc}'
   valid_date = open(f'{fol}/valid_date.txt','r').read().strip()
   valid_date = dt.datetime.strptime(valid_date, '%d/%m/%Y')
   valid_date = valid_date.replace(hour=date.hour,minute=date.minute)
   grids_fol = RP.fol_grids
   f_tmp = '/tmp/' + rand_name() + '.png'
   f_tmp1 = '/tmp/' + rand_name() + '.png'
   hora = dateUTC.strftime('%H00')
   title = f"{valid_date.strftime('%d/%m/%Y-%H:%M')} {prop_names[scalar]}"
   terrain = f'{fol}/terrain.png'
   rivers = f'{fol}/rivers.png'
   ccaa = f'{fol}/ccaa.png'
   takeoffs = f'{fol}/takeoffs.png'
   cities = f'{fol}/cities.png'
   manga = f'{fol}/manga.png'
   bar = f'{root_fol}/{scalar}.png'  #_light.png'
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
   cities = mpimg.imread(cities)
   try: manga = mpimg.imread(manga)
   except FileNotFoundError: pass
   if vector != None: img_vector = mpimg.imread(vector)
   img_scalar = mpimg.imread(scalar)
   bar = mpimg.imread(bar)
   # Output Images
   fig = plt.figure()
   COLOR = 'black'
   COLOR = '#e0e0e0'
   mpl.rcParams['text.color'] = COLOR
   mpl.rcParams['axes.labelcolor'] = COLOR
   mpl.rcParams['axes.facecolor'] = 'black'
   mpl.rcParams['savefig.facecolor'] = 'black'
   mpl.rcParams['xtick.color'] = COLOR
   mpl.rcParams['ytick.color'] = COLOR
   mpl.rcParams['axes.edgecolor'] = COLOR

   gs = gridspec.GridSpec(2, 1, height_ratios=[7.2,1])
   fig.subplots_adjust(wspace=0.,hspace=0.)
   ax1 = plt.subplot(gs[0,0])
   ax2 = plt.subplot(gs[1,0])
   ax1.imshow(terrain,aspect=aspect,interpolation='lanczos',zorder=0)
   ax1.imshow(rivers,aspect=aspect,interpolation='lanczos',zorder=0)
   ax1.imshow(ccaa,aspect=aspect,interpolation='lanczos',zorder=20)
   ax1.imshow(takeoffs,aspect=aspect,interpolation='lanczos',zorder=20)
   ax1.imshow(cities,aspect=aspect,interpolation='lanczos',zorder=20)
   if vector != None:
      ax1.imshow(img_vector, aspect=aspect, interpolation='lanczos',
                             zorder=11, alpha=0.75)
   ax1.imshow(img_scalar, aspect=aspect, interpolation='lanczos',
                          zorder=10, alpha=0.5)
   try: ax1.imshow(manga,aspect=aspect,interpolation='lanczos',zorder=21)
   except: pass
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
   return f_tmp, valid_date


def send_sounding(place,date,bot,chatID,job_queue, userID,
                                                   t_del=RP.t_del,  #5*60,
                                                   t_renew=6*60*60,
                                                   dis_notif=False):
   LG.debug('Sending sounding {place} {date}')
   places = {'arcones': 1, 'bustarviejo': 2, 'cebreros': 3, 'abantos': 4,
             'piedrahita': 5, 'pedro bernardo': 6, 'lillo': 7,
             'fuentemilanos': 8, 'candelario': 10, 'pitolero': 11,
             'pegalajar': 12, 'otivar': 13}
   index = places[place]
   tmp_folder = '/tmp'
   f_tmp = '/tmp/' + rand_name()
   if isinstance(date,dt.datetime):
      LG.debug('Sending single sounding')
      fol = get_sc(date.date())
      # dateUTC = date - get_utc_shift()
      places = {'arcones': 1, 'bustarviejo': 2, 'cebreros': 3, 'abantos': 4,
                'piedrahita': 5, 'pedro bernardo': 6, 'lillo': 7,
                'fuentemilanos': 8, 'candelario': 10, 'pitolero': 11,
                'pegalajar': 12, 'otivar': 13}
      index = places[place]
      H = date.strftime('%H%M')
      url_picture = 'http://raspuri.mooo.com/RASP/'
      url_picture += f'{fol}/FCST/sounding{index}.curr.{H}lst.w2.png'
      LG.debug(url_picture)
      urlretrieve(url_picture, f'{f_tmp}.png')
      T,url = aemet.get_temp(place,date)
      fmt = '%d/%m/%Y-%H:%M'
      txt = f"Sounding for _{place.capitalize()}_ at {date.strftime(fmt)}"
      if T != None:
         txt += f'\nExpected temperature: *{T}°C*\n'
         # txt += 'Temperatura sacada de aemet:\n'
         # txt += url.replace('_','\_')
         disable_web_page_preview = True
      else:
         disable_web_page_preview = None
      P =  PlotDescriptor(date,None,None,None,fname=f'{f_tmp}.png')
   elif isinstance(date,dt.date):
      LG.debug('Sending sounding video')
      fol = get_sc(date)
      f_out = f"{tmp_folder}/sounding_{place.replace(' ','_')}.mp4"
      i = 0
      for H in range(8,20):
         # H = date.strftime('%H%M')
         url_picture = 'http://raspuri.mooo.com/RASP/'
         url_picture += f'{fol}/FCST/sounding{index}.curr.{H*100:04d}lst.w2.png'
         A = urlretrieve(url_picture, f_tmp + f'_{i:04d}.png')
         i += 1
      # com = f'ffmpeg -i {f_tmp}_%02d.png output.gif'
      f_gif = f'{f_tmp}.gif'
      com =  f'convert -delay 150 -quality 20 -size 200 -loop 0'
      com += f'  {f_tmp}_*.png {f_gif}'
      com += f' > /dev/null 2> /dev/null'
      os.system(com)
      com = f'ffmpeg -i {f_gif} -movflags faststart -pix_fmt yuv420p'
      com += f' -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" {f_out}'
      com += f' > /dev/null 2> /dev/null'
      os.system(com)
      com = f'rm {f_tmp}_*.png {f_gif}'
      os.system(com)
      txt = f"Curva de estado para {place.capitalize()}"
      txt += f" {date.strftime('%d/%m/%Y')}"
      txt += '\nPuedes ver la evolución de temperatura:\n'
      txt += aemet.get_place_horas(place)
      P =  PlotDescriptor(date,None,None,None,fname=f_out)
   else: LG.critical(f'Error in sounding with time. Recived: {date}')
   # Send prepared media
   send_media(bot,chatID,job_queue, P, userID, caption=txt,
                                       t_del=RP.t_del,  #5*60,
                                       t_renew=6*60*60,
                                       dis_notif=False,recycle=False,rm=True,
                                       disable_web_page_preview = None)

def send_aemet(date,prop,bot,chatID,job_queue, t_del=5*60,t_renew=6*60*60,
                                                   dis_notif=False):
   """
   Send Aemet's forecast for rain [around Madrid]
   """
   captions = {'rain':'LLuvia acumulada en 1h',
               'clouds':'Nubosidad','temperature':'Temperatura',
               'press':'Presión', 'wind':'Viento',
               'gust':'Racha máxima', 'lightning':'Descargas eléctricas'}
   url = aemet.modelo_numerico(prop,date)
   f_tmp = '/tmp/' + rand_name() + '.png'
   try: urlretrieve(url, f_tmp)
   except HTTPError:
      txt = 'Lo siento, el pronóstico que has pedido no está disponible\n'
      txt += 'Puedes comprobar las horas disponibles aquí:\n'
      txt += 'https://www.aemet.es/es/eltiempo/prediccion/modelosnumericos/'
      txt += 'harmonie_arome_ccaa?opc2=mad&opc3=pr'
      bot.send_message(chat_id=chatID, text=txt)
      return
   P =  PlotDescriptor(date,None,None,None,fname=f_tmp)
   txt = f"{captions[prop]} para el {date.strftime('%d/%m/%Y-%H:00')}\n"
   txt += 'Sacada de Aemet:\n'
   txt += 'https://www.aemet.es/es/eltiempo/prediccion/modelosnumericos/'
   txt += 'harmonie_arome_ccaa?opc2=mad&opc3=pr'
   txt = txt.replace('_','\_')
   send_media(bot,chatID,job_queue, P, caption=txt,
                                       t_del=RP.t_del,  #5*60,
                                       t_renew=6*60*60,
                                       dis_notif=False, recycle=False)
   os.system(f'rm {f_tmp}')


def get_utc_shift():
   UTCshift = dt.datetime.now()-dt.datetime.utcnow()
   return dt.timedelta(hours = round(UTCshift.total_seconds()/3600))

def get_sc(date):
   """
   returns the corresponding SCfolder:
     today: SC2
     tomorrow: SC2+1
     ...
   date should be a dt.date
   """
   day = dt.timedelta(days=1)
   now = dt.datetime.now().date()
   if   date == now: return 'SC2'
   elif date == now+day: return 'SC2+1'
   elif date == now+2*day: return 'SC4+2'
   elif date == now+3*day: return 'SC4+3'
   else: return None



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
   txt =  f"/sfcwind - Viento en superficie\n"
   txt += f"/bltopwind - Viento en el tope de la capa convectiva\n"
   txt += f"/blwind - Viento promedio de toda la capa convectiva\n"
   txt += f"/techo - Altura máxima de las térmicas (en días de térmica azul)\n"
   txt += f"/base\\_nube - Altura de la base de los cúmulos\n"
   txt += f"/cubierta\\_nube - Altura de la base de la cobertura de nubes (8/8)\n"
   txt += f"/termicas - Potencia máxima de las térmicas\n"
   txt += f"/convergencias - Velocidad vertical máxima del viento (ignorando térmicas)\n"
   txt += f"/lluvia - Lluvia acumulada en 1 hora (sacada de Aemet)\n"
   txt += f"/map - Mapa personalizado, combinando el flujo de viento deseado con cualquier otra propiedad\n"
   txt += f"/sondeo - Curva de estado\n"
   txt += f"/aemet - Modelos numéricos de Aemet (HARMONIE-AROME)\n"
   txt += f"/meteograma - Meteograma para los despegues o para una ubicación personalizada\n"
   txt += f"/feedback - Manda un mensaje al creador del bot\n"
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
   txt = '\n'.join(tail(RP.log))
   txt = f'```\n{txt}\n```'
   M = context.bot.send_message(chatID, text=txt, 
                                parse_mode=ParseMode.MARKDOWN)

@CR.restricted(3)
def feedback(update, context):
   """ echo-like service to check system status """
   args = ' '.join(context.args)
   if len(args) == 0:
      try: chatID = update['message']
      except TypeError: chatID = update['callback_query']['message']
      chatID = chatID['chat']['id']
      txt = 'Si quieres enviar algún comentario al autor tienes que incluirlo en el mensaje, por ejemplo:\n'
      txt += '`/feedback He tenido un error al usar...`'
      M = context.bot.send_message(chatID, text=txt, 
                                   parse_mode=ParseMode.MARKDOWN)
      return
   chat = update['message']['chat']
   uname = chat['username']
   fname = chat['first_name']
   lname = chat['last_name']
   txt = f'Message from {fname} {lname} ({uname}):\n'
   txt += args
   LG.info('Sending feedback!')
   chatID = MB.me
   M = context.bot.send_message(chatID, text=txt, 
                                parse_mode=ParseMode.MARKDOWN)


import meteograms
def meteogram(date,info,bot,chatID,job_queue,userID,dpi=65):
   places = {'somosierra':(-3.615281,41.149850),
             'arcones':(-3.707029,41.078854),
             'nevero':(-3.847430,40.982414),
             'bustarviejo':(-3.68661,40.87575),
             'torrecaballeros':(-4.000919,40.937505),
             'abantos':(-4.154882,40.611774),
             'cebreros':(-4.51,40.45),
             'pedro bernardo':(-4.91,40.25 ),
             'piedrahita':(-5.3015,40.4221),
             'lastra del cano':(-5.444265,40.346122),
             'fuentemilanos':(-4.239,40.889),
             'candelario':(-5.744,40.365)}
   try:
      P0 = places[info['place']]
      place_name = info['place'].capitalize()
   except KeyError:
      P0 = info['place']
      place_name = ''
   data_fol = RP.fol_data
   grids = RP.fol_grids
   terrain = RP.fol_grids.replace('grids','terrain')
   f_tmp = '/tmp/' + rand_name() + '.png'
   stat = meteograms.get_meteogram(P0,date,data_fol,grids,terrain,f_tmp,
                                                           place_name=place_name)
   if stat:
      P =  PlotDescriptor(date,None,None,None,fname=f_tmp)
      txt = f'Meteograma en {place_name} para {date}'
      send_media(bot,chatID,job_queue, P, userID, caption=txt,
                                          t_del=RP.t_del,  #5*60,
                                          t_renew=6*60*60,
                                          dis_notif=False,
                                          recycle=False,rm=True)
   else:
      txt = 'Creo que me has pasado un punto fuera de nuestro domino de cálculo. No hay nada que pueda hacer, lo siento.'
      bot.send_message(chat_id=chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
