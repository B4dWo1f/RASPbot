#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import aemet
import credentials as CR
from telegram.ext import Updater
from telegram.ext import CommandHandler as CH
from telegram.ext import MessageHandler, Filters, ConversationHandler
from telegram.ext import CallbackQueryHandler as CQH
from threading import Thread
import sounding_menu as sm
import datetime as dt
import tool
import sys
import os
here = os.path.dirname(os.path.realpath(__file__))

import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s:%(levelname)s - %(message)s',
                    datefmt='%Y/%m/%d-%H:%M:%S',
                    filename=here+'/main.log', filemode='w')

LG = logging.getLogger('main')


def start(bot, update):
   txt = "I'm a bot, please talk to me!"
   bot.send_message(chat_id=update.message.chat_id, text=txt)

def shutdown():
   U.stop()
   U.is_idle = False

@CR.restricted
def stop(bot, update):
   chatID = update.message.chat_id
   txt = 'I\'ll be shutting down\nI hope to see you soon!'
   bot.send_message(chatID, text=txt, parse_mode='Markdown')
   Thread(target=shutdown).start()

def stop_and_restart():
   """
   Gracefully stop the Updater and replace the current process with a new one
   """
   U.stop()
   os.execl(sys.executable, sys.executable, *sys.argv)


@CR.restricted
def restart(bot,update):
   txt = 'Bot is restarting...'
   chatID = update.message.chat_id
   bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')
   Thread(target=stop_and_restart).start()



def broadcast(bot, job):
   """ Broadcast information to a given chat """
   LG.info('Starting automatic 12:00 broadcast')
   now = dt.datetime.now()
   tday = now.date()
   if now.hour == 7: hours = [9,12,17,19]
   elif now.hour == 10: hours = [12,17,19]
   elif now.hour == 12: hours = [12,17,19]
   elif now.hour == 18: hours = [17,19]
   else: raise
   for h in hours:
      d = dt.datetime.combine(tday, dt.time(h, 0))
      LG.info('Broadcasting forecast for '+d.strftime('%H:%M'))
      _,f = tool.locate(d, 'sfcwind')
      txt = 'Surface wind at *%s*\n'%(d.strftime('%H:%M'))
      txt += 'For more information go to:\n'
      txt += ' http://raspuri.mooo.com/RASP/index.php'
      tool.send_picture(bot, Bcast_chatID, J, f, msg=txt,
                                          t=5*3600, delete=True, dis_notif=True)
   if now.hour == 7:
      places = ['gre1', 'mad2']
      w = 2
      txt = 'AVISOS DE TORMENTA'
      for p in places:
         url = f'http://www.aemet.es/es/eltiempo/prediccion/montana?w={w}&p={p}'
         P = aemet.parse_parte_aemet(url)
         if P.storm != 'No se esperan':
            txt += '\n'+ str(P)
            M = bot.send_message(Bcast_chatID, text=txt, parse_mode='Markdown')
            txt = ''
      if txt == 'AVISOS DE TORMENTA': txt += ': No se esperan'
      M = bot.send_message(Bcast_chatID, text=txt, parse_mode='Markdown')

#def check_storms(bot, job):
#   """
#   Check the storms forecast from aemet.
#   """
#   places = ['gre1', 'mad2']
#   w = 2
#   txt = 'AVISOS DE TORMENTA'
#   for p in places:
#      url = f'http://www.aemet.es/es/eltiempo/prediccion/montana?w={w}&p={p}'
#      P = aemet.parse_parte_aemet(url)
#      if P.storm != 'No se esperan':
#         txt += '\n'+ str(P)
#         M = bot.send_message(Bcast_chatID, text=txt, parse_mode='Markdown')
#         txt = ''
#   if txt == 'AVISOS DE TORMENTA': txt += 'No se esperan'
#   M = bot.send_message(Bcast_chatID, text=txt, parse_mode='Markdown')



# Start Bot
token, Bcast_chatID = CR.get_credentials('rasp.token')

U = Updater(token=token)
D = U.dispatcher
J = U.job_queue

## Add Handlers
# Start
D.add_handler(CH('start', start))
# Re-Load
D.add_handler(CH('reload', restart))
# Stop
D.add_handler(CH('stop', stop))
# Hola
D.add_handler(CH('hola', tool.hola))
# Forecast
D.add_handler(CH('fcst', tool.fcst, pass_args=True, pass_job_queue=True))
# Surface Wind
D.add_handler(CH('sfcwind', tool.sfcwind, pass_args=True, pass_job_queue=True))
# BL Wind
D.add_handler(CH('blwind', tool.blwind, pass_args=True, pass_job_queue=True))
# top BL Wind
D.add_handler(CH('bltopwind', tool.bltopwind, pass_args=True, pass_job_queue=True))
# CAPE
D.add_handler(CH('cape', tool.cape, pass_args=True, pass_job_queue=True))
# Techo
D.add_handler(CH('techo', tool.techo, pass_args=True, pass_job_queue=True))
# Thermal
D.add_handler(CH('thermal', tool.thermal, pass_args=True, pass_job_queue=True))
## Sounding
#D.add_handler(CH('sounding', tool.sounding, pass_args=True, pass_job_queue=True))
# Tormentas
D.add_handler(CH('tormentas', tool.tormentas, pass_args=True, pass_job_queue=True))

## Conversation Handler ########################################################
conversation_handler = ConversationHandler(
      entry_points=[CH('sounding', sm.choose_place, pass_user_data=True)],
      states={'SOU_PLACE': [CQH(sm.choose_date, pass_user_data=True)],
              'SOU_TIME': [CQH(sm.choose_time, pass_user_data=True)],
              'SOU_SEND': [CQH(sm.send,pass_user_data=True,pass_job_queue=True)]},
      fallbacks = [CH('sounding', sm.choose_place, pass_user_data=True)])
D.add_handler(conversation_handler)
################################################################################


J.run_daily(broadcast, dt.time(7,58))
J.run_daily(check_storms, dt.time(10,38))
J.run_daily(broadcast, dt.time(12,48))
J.run_daily(broadcast, dt.time(18,18))


U.start_polling()
U.idle()
