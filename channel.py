#!/usr/bin/python3
# -*- coding: UTF-8 -*-

# Telegram libraries
from telegram import ChatAction, ParseMode
import aemet

import numpy as np
import datetime as dt
from urllib.request import urlretrieve
from urllib.error import HTTPError
import os
here = os.path.dirname(os.path.realpath(__file__))
HOME = os.getenv('HOME')
import logging
LG = logging.getLogger(__name__)


def make_frentes_gif(vidname='/tmp/frentes.mp4'):
   now = dt.datetime.now()
   day = dt.timedelta(days=1)
   base = 'http://www.aemet.es/imagenes_d/eltiempo/prediccion/mapa_frentes/'
           #--- Hoy ---
   urls = [base + now.strftime('%Y%m%d')+'00+000_ww_gpx0a000.gif',
           base + (now-day).strftime('%Y%m%d')+'12+024_ww_g1x0a2d1.gif',
           #--- Mañana ---
           base + (now-day).strftime('%Y%m%d')+'12+036_ww_g1x0a2c1.gif',
           base + (now-day).strftime('%Y%m%d')+'12+048_ww_g1x0a2d2.gif',
           #--- Pasado ---
           base + (now-day).strftime('%Y%m%d')+'12+060_ww_g1x0a2c2.gif',
           base + (now-day).strftime('%Y%m%d')+'12+072_ww_g1x0a2d3.gif']
   f = open('/tmp/files.txt','w')
   fps = 1
   N = 2
   fails = []
   for i,url in enumerate(urls):
      try:
         a = urlretrieve(url, f'/tmp/frentes_{i}.gif')
         os.system(f'convert /tmp/frentes_{i}.gif /tmp/frentes_{i}.jpg')
         os.system(f'rm /tmp/frentes_{i}.gif')
         for _ in range(N):
            f.write(f'/tmp/frentes_{i}.jpg\n')
         fails.append(True)
      except HTTPError:
         fails.append(False)
         continue
   f.close()
   tmp_file = '/tmp/files.txt'
   com = f'mencoder -quiet -nosound -ovc lavc -lavcopts vcodec=mpeg4'
   com += f' -o /tmp/frentes_temp.mp4'
   com += f' -mf type=jpeg:fps={max([1,int(fps/N)])} mf://@{tmp_file}'
   com += ' > /dev/null 2> /dev/null'
   os.system(com)
   com =  f'ffmpeg -y -i /tmp/frentes_temp.mp4 -vcodec mpeg4 -threads 2'
   com += f' -b:v 1500k -acodec libmp3lame -ab 160k {vidname}'
   com += ' > /dev/null 2> /dev/null'
   os.system(com)
   os.system(f'rm /tmp/frentes_*.jpg /tmp/frentes_temp.mp4')
   return all(fails)


def send_frentes(chatID,bot):
   """ Create gif with the forecasts for pressure for the next days """
   vid = '/tmp/frentes.mp4'
   make_frentes_gif(vid)
   now = dt.datetime.now()
   tday = now.date()
   LG.info(f"Sending frentes")
   txt = ' http://www.aemet.es/es/eltiempo/prediccion/mapa\_frentes'
   video = open(vid, 'rb')
   bot.send_chat_action(chatID, action=ChatAction.UPLOAD_VIDEO)
   M = bot.send_video(chatID,video, caption=txt, timeout=300,
                                               disable_notification=True,
                                               parse_mode=ParseMode.MARKDOWN)
   LG.debug(f"frentes sent")
   os.system(f'rm {vid}')


def send_sfcwind(chatID,bot):
   """ Send video of sfcwind for the day """
   LG.info(f"Sending sfcwind of the day")
   now = dt.datetime.now()
   tday = now.date()
   txt = 'Surface wind for *%s*\n'%(tday.strftime('%d/%m/%Y'))
   #txt += ' http://raspuri.mooo.com/RASP/index.php'
   txt = ' http://meteonube.hopto.org'
   vid = f'{HOME}/Documents/RASP/PLOTS/w2/SC2/sfcwind.mp4'
   vid = open(vid, 'rb')
   bot.send_chat_action(chatID, action=ChatAction.UPLOAD_VIDEO)
   M = bot.send_video(chatID,vid, caption=txt,
                             timeout=300, disable_notification=True,
                             parse_mode=ParseMode.MARKDOWN)
   LG.debug(f"sfcwind sent")


def send_tormentas(chatID,bot):
   """ Check Aemet forecast for storms of Gredos and Guadarrama """
   LG.info(f"Checking tormentas")
   places = ['gre1', 'mad2']
   w = 2
   txt = 'AVISOS DE TORMENTA'
   for p in places:
      url = f'http://www.aemet.es/es/eltiempo/prediccion/montana?w={w}&p={p}'
      P = aemet.parse_parte_aemet(url)
      if P.storm != 'No se esperan':
         txt += '\n'+ '`' + str(P) + '`'
         M = bot.send_message(chatID, text=txt, disable_notification=True,
                                      parse_mode=ParseMode.MARKDOWN)
         txt = ''
   if txt == 'AVISOS DE TORMENTA':
      txt += ': `No se esperan`'
      M = bot.send_message(chatID, text=txt, disable_notification=True,
                                   parse_mode=ParseMode.MARKDOWN)
   LG.debug('tormentas sent')


def send_poll(chatID,bot, ftmp='mypoll.txt'):
   """ Send poll to recollect data on bet flyiability conditions """
   LG.info('send poll')
   # Poll
   A = bot.send_poll(chatID, 'Dónde irías hoy a volar?',
                             ['Arcones', 'Somosierra', 'Mondalindo', 'Abantos',
                              'Cebreros', 'Pedro Bernardo', 'Piedrahita',
                              'Hoy no se vuela'],
                             disable_notification=True)
   #TODO probably there's a proper way to do this
   LG.debug(f'saving message to delete in {ftmp}')
   with open(ftmp,'w') as f:
      f.write(f"{A['message_id']}\n")
   LG.debug('poll sent')


def broadcast(context):
   """
   Broadcast daily information to a given chat.
   It sends a video with the surface wind and the storms forecast.
   """
   LG.info('Starting broadcast of the day')
   Bcast_chatID, = context.job.context
   job = context.job
   bot = context.bot
   now = dt.datetime.now()
   tday = now.date()
   send_frentes(Bcast_chatID, bot)
   # send_sfcwind(Bcast_chatID, bot)
   send_tormentas(Bcast_chatID, bot)
   # send_poll(Bcast_chatID, bot, ftmp='mypoll.txt')
   LG.info('Finished broadcast of the day')



def close_poll(context):
   LG.info(f"Closing poll")
   Bcast_chatID, = context.job.context
   job = context.job
   bot = context.bot
   msg_id = open('mypoll.txt','r').read().strip()
   results = context.bot.stop_poll(Bcast_chatID, msg_id)
   LG.info('Saving results')
   # Save results
   opts = [f"{x['text']}:{x['voter_count']}" for x in results['options']]
   now = dt.datetime.now()
   with open('meteo_survey.data','a') as f:
      f.write(now.date().strftime('%d/%m/%Y')+',')
      f.write(','.join(opts))
      f.write('\n')
   f.close()
   #m = bot.edit_message_text('Replacement', chat_id=Bcast_chatID, message_id=msg_id)
   m = context.bot.delete_message(Bcast_chatID, msg_id)
   places,votes = [],[]
   for opt in results['options']:
      places.append(opt['text'])
      votes.append(opt['voter_count'])
   votes_pct = (np.array(votes)/np.sum(votes))*100
   inds = np.argsort(votes_pct)
   now = dt.datetime.now()
   txt = [f"Resultados día {now.strftime('%d/%m/%Y')}\n"]
   for i in reversed(inds[-3:]):
      txt.append(f' `{places[i]}: {votes_pct[i]}`')
   txt = '\n'.join(txt)
   M = bot.send_message(Bcast_chatID, text=txt, disable_notification=True,
                                parse_mode=ParseMode.MARKDOWN)




if __name__ == '__main__':
   make_frentes_gif()
