#!/usr/bin/python3
# -*- coding: UTF-8 -*-

## Telegram libraries
from telegram.ext import MessageHandler, Filters, ConversationHandler
from telegram.ext import CallbackQueryHandler as CQH
from telegram.ext import CommandHandler as CH
from telegram import ChatAction, ParseMode
from telegram.ext import Updater
# Telegram custom libraries
import sounding_menu as sm
import credentials as CR
import channel
import admin
import aemet
import tool
## System libraries
import datetime as dt
from threading import Thread
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


# Start Bot ####################################################################
token, Bcast_chatID = CR.get_credentials(here+'/rasp.token')
token, Bcast_chatID = CR.get_credentials(here+'/Tester.token')

U = Updater(token=token, use_context=True)
D = U.dispatcher
J = U.job_queue

## Add Handlers
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
# Clouds
D.add_handler(CH('clouds', tool.blcloud, pass_args=True, pass_job_queue=True))
# Tormentas
D.add_handler(CH('tormentas', tool.tormentas, pass_args=True, pass_job_queue=True))
## Secret admin commands
# Start
D.add_handler(CH('start', start))
# Re-Load
D.add_handler(CH('reload', restart))
# Stop
D.add_handler(CH('stop', stop))
# Hola
D.add_handler(CH('hola', tool.hola))


## Conversation Handler ########################################################
conversation_handler = ConversationHandler(
      entry_points=[CH('sounding', sm.choose_place, pass_user_data=True)],
      states={'SOU_PLACE': [CQH(sm.choose_date, pass_user_data=True)],
              'SOU_TIME': [CQH(sm.choose_time, pass_user_data=True)],
              'SOU_SEND': [CQH(sm.send,pass_user_data=True,pass_job_queue=True)]},
      fallbacks = [CH('sounding', sm.choose_place, pass_user_data=True)])
D.add_handler(conversation_handler)
################################################################################

## Setup DB for files ##########################################################
admin.create_db('RaspBot.db')

# Broadcast
J.run_daily(channel.broadcast, dt.time(9,0), context=(Bcast_chatID,))
J.run_daily(channel.close_poll, dt.time(23,50), context=(Bcast_chatID,)) 


U.start_polling()
U.idle()
