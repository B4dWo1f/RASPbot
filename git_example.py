#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards.
"""
import logging

import credentials as CR
import os
import sys
from threading import Thread
from telegram import ChatAction, ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

## STOP bot ####################################################################
def shutdown():
   updater.stop()
   updater.is_idle = False

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
   updater.stop()
   os.execl(sys.executable, sys.executable, *sys.argv)


@CR.restricted
def restart(update,context):
   """ Reload the Bot to update code, for instance """
   txt = 'Bot is restarting...'
   chatID = update['message']['chat']['id']
   context.bot.send_message(chat_id=chatID, text=txt, 
                            parse_mode=ParseMode.MARKDOWN)
   Thread(target=stop_and_restart).start()
################################################################################


def map_selector(update, context):
   chatID = update['message']['chat']['id']
   txt = 'Please choose layers for the map'
   context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)

   keyboard = [[InlineKeyboardButton("Superficie", callback_data='sfcwind'),
                InlineKeyboardButton("Media Altura", callback_data='blwind'),
                InlineKeyboardButton("Altura", callback_data='bltopwind')],
               [InlineKeyboardButton("Ninguno", callback_data='none')]]
   reply_markup = InlineKeyboardMarkup(keyboard)
   update.message.reply_text('Flujo de viento', reply_markup=reply_markup)

def day_selector(update, context):
   chatID = update['message']['chat']['id']
   txt = 'Please choose layers for the map'
   context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)

   keyboard = [[InlineKeyboardButton("Hoy", callback_data='SC2'),
                InlineKeyboardButton("Mañana", callback_data='SC2+1')],
               [InlineKeyboardButton("Pasado", callback_data='SC4+2'),
               InlineKeyboardButton("Al otro", callback_data='SC4+3')]]
   reply_markup = InlineKeyboardMarkup(keyboard)
   update.message.reply_text('Dia', reply_markup=reply_markup)
   print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
   query = update.callback_query
   query.edit_message_text(text="Selected option: {}".format(query.data))
   print('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')

def button(update, context):
   print('Button original')
   query = update.callback_query
   query.edit_message_text(text="Selected option: {}".format(query.data))

def button1(update, context):
   print('Button one')
   query = update.callback_query
   query.edit_message_text(text="Selected option: {}".format(query.data))



def help(update, context):
    update.message.reply_text("Use /map to test this bot.")



def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


## MAIN ########################################################################
# Create the Updater and pass it your bot's token.
# Make sure to set use_context=True to use the new context based callbacks
# Post version 12 this will no longer be necessary
token, Bcast_chatID = CR.get_credentials('Tester.token')
updater = Updater(token, use_context=True)

updater.dispatcher.add_handler(CommandHandler('map', map_selector))
updater.dispatcher.add_handler(CallbackQueryHandler(button1))
updater.dispatcher.add_handler(CallbackQueryHandler(button))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('reload', restart))
updater.dispatcher.add_handler(CommandHandler('stop', stop))
updater.dispatcher.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()
