#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import aemet
import credentials as CR
from telegram import ChatAction, ParseMode
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
HOME = os.getenv('HOME')
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s:%(levelname)s - %(message)s',
                    datefmt='%Y/%m/%d-%H:%M:%S',
                    filename=here+'/main.log', filemode='w')

LG = logging.getLogger('main')


def start(update, context):
   txt = "I'm a bot, please talk to me!"
   context.bot.send_message(chat_id=update.message.chat_id, text=txt)

def shutdown():
   U.stop()
   U.is_idle = False

#def stop(bot, update):
@CR.restricted
def stop(update, context):
   """ Completely halt the Bot """
   chatID = update['message']['chat']['id']
   txt = 'I\'ll be shutting down\nI hope to see you soon!'
   context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
   Thread(target=shutdown).start()

def stop_and_restart():
   """
   Gracefully stop the Updater and replace the current process with a new one
   """
   U.stop()
   os.execl(sys.executable, sys.executable, *sys.argv)


@CR.restricted
def restart(update,context):
   """ Reload the Bot to update code, for instance """
   txt = 'Bot is restarting...'
   chatID = update['message']['chat']['id']
   context.bot.send_message(chat_id=chatID, text=txt, 
                            parse_mode=ParseMode.MARKDOWN)
   Thread(target=stop_and_restart).start()



def broadcast(context): #(bot, job):
   """
   Broadcast daily information to a given chat.
   It sends a video with the surface wind and the storms forecast.
   """
   ftmp = 'mypoll.txt'
   job = context.job
   now = dt.datetime.now()
   tday = now.date()
   LG.info(f"Starting automatic {now.strftime('%H:%M')} broadcast")
   vid = f'{HOME}/Documents/RASP/PLOTS/w2/SC2/sfcwind.mp4'
   txt = 'Surface wind for *%s*\n'%(tday.strftime('%d/%m/%Y'))
   txt += 'For more information go to:\n'
   txt += ' http://raspuri.mooo.com/RASP/index.php'
   #txt += ' http://meteonube.hopto.org'
   #M = tool.send_video(update,context, J, vid, msg=txt, t=3*3600,
   #                              delete=True, dis_notif=True, warn_wait=False)
   vid = open(vid, 'rb')
   LG.info(f"Sending the forecast of the day")
   context.bot.send_chat_action(Bcast_chatID, action=ChatAction.UPLOAD_VIDEO)
   M = context.bot.send_video(Bcast_chatID,vid, caption=txt,
                              timeout=300, disable_notification=True,
                              parse_mode=ParseMode.MARKDOWN)
   LG.debug(f"forecast of the day sent")
   if True: #now.hour == 8:
      places = ['gre1', 'mad2']
      w = 2
      txt = 'AVISOS DE TORMENTA'
      for p in places:
         url = f'http://www.aemet.es/es/eltiempo/prediccion/montana?w={w}&p={p}'
         P = aemet.parse_parte_aemet(url)
         if P.storm != 'No se esperan':
            txt += '\n'+ str(P)
            M = context.bot.send_message(Bcast_chatID, text=txt,
                                         disable_notification=True,
                                         parse_mode=ParseMode.MARKDOWN)
            txt = ''
      if txt == 'AVISOS DE TORMENTA':
         txt += ': No se esperan'
         M = context.bot.send_message(Bcast_chatID, text=txt,
                                      disable_notification=True,
                                      parse_mode=ParseMode.MARKDOWN)

   # Poll
   A = context.bot.send_poll(Bcast_chatID, 'Dónde irías hoy a volar?',
                             ['Arcones', 'Somosierra', 'Mondalindo', 'Abantos',
                              'Cebreros', 'Pedro Bernardo', 'Piedrahita',
                              'Hoy no se vuela'],
                             disable_notification=True)
   #TODO probably there's a proper way to do this
   LG.debug(f'saving message to delete in {ftmp}')
   with open(ftmp,'w') as f:
      #f.write(A['poll']['id']+' '+A['message_id']+'\n')
      f.write(f"{A['message_id']}\n")


from telegram import Poll
def close_poll(context):
   LG.info(f"Closing poll")
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



# Start Bot ####################################################################
token, Bcast_chatID = CR.get_credentials(here+'/rasp.token')
token, Bcast_chatID = CR.get_credentials('../SYSbot/Tester.token')
Bcast_chatID = -379078023

U = Updater(token=token, use_context=True)
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
# Surface Wind
D.add_handler(CH('sfcwind', tool.sfcwind, pass_args=True, pass_job_queue=True))
# BL Wind
D.add_handler(CH('blwind', tool.blwind, pass_args=True, pass_job_queue=True))
# top BL Win
D.add_handler(CH('bltopwind', tool.bltopwind, pass_args=True, pass_job_queue=True))
# CAPE
D.add_handler(CH('cape', tool.cape, pass_args=True, pass_job_queue=True))
# Techo
D.add_handler(CH('techo', tool.techo, pass_args=True, pass_job_queue=True))
# Thermal
D.add_handler(CH('thermal', tool.thermal, pass_args=True, pass_job_queue=True))
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


# Broadcast
J.run_daily(broadcast, dt.time(9,0))
#J.run_daily(broadcast, dt.time(13,00))
#J.run_daily(broadcast, dt.time(15,55))
#J.run_daily(broadcast, dt.time(18,15))
J.run_daily(close_poll, dt.time(21,30))


U.start_polling()
U.idle()
