#!/usr/bin/python3
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardButton as IlKB
from telegram import ChatAction, ParseMode
import datetime as dt
import tool
import credentials as CR
from threading import Thread
import os
import sys
############################### Bot ############################################
# def start(bot, update):
def start(update,context):
   update.message.reply_text(main_menu_message(),
                             reply_markup=main_menu_keyboard())

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

# Main ######################################################################
def main_menu(update,context):
   print('****************')
   bot = context.bot
   query = update.callback_query
   bot.edit_message_text(chat_id=query.message.chat_id,
                         message_id=query.message.message_id,
                         text=main_menu_message(),
                         reply_markup=main_menu_keyboard())
   print('here')

# def first_menu(bot, update):
#   query = update.callback_query
#   bot.edit_message_text(chat_id=query.message.chat_id,
#                         message_id=query.message.message_id,
#                         text=first_menu_message(),
#                         reply_markup=first_menu_keyboard())

# def second_menu(bot, update):
#   query = update.callback_query
#   bot.edit_message_text(chat_id=query.message.chat_id,
#                         message_id=query.message.message_id,
#                         text=second_menu_message(),
#                         reply_markup=second_menu_keyboard())

# # and so on for every callback_data option
# def first_submenu(bot, update):
#   pass

# def second_submenu(bot, update):
#   pass

############################ Keyboards #########################################
def main_menu_keyboard():
   print('hheeeyyyyy')
   # keyboard = [[InlineKeyboardButton('AOption 1', callback_data='m1')],
   #             [InlineKeyboardButton('AOption 2', callback_data='m2')],
   #             [InlineKeyboardButton('AOption 3', callback_data='m3')]]
   now = dt.datetime.now()
   day = dt.timedelta(days=1)
   fmt = '%d/%m/%Y'
   print(now,fmt)
   keyboard = [[IlKB("Hoy", callback_data=now.strftime(fmt)),
                IlKB("Mañana", callback_data=(now+day).strftime(fmt))],
               [IlKB("Pasado", callback_data=(now+2*day).strftime(fmt)),
                IlKB("Al otro", callback_data=(now+3*day).strftime(fmt))] ]
   print(keyboard)
   return InlineKeyboardMarkup(keyboard)

# def first_menu_keyboard():
#   keyboard = [[InlineKeyboardButton('Submenu 1-1', callback_data='m1_1')],
#               [InlineKeyboardButton('Submenu 1-2', callback_data='m1_2')],
#               [InlineKeyboardButton('Main menu', callback_data='main')]]
#   return InlineKeyboardMarkup(keyboard)

# def second_menu_keyboard():
#   keyboard = [[InlineKeyboardButton('Submenu 2-1', callback_data='m2_1')],
#               [InlineKeyboardButton('Submenu 2-2', callback_data='m2_2')],
#               [InlineKeyboardButton('Main menu', callback_data='main')]]
#   return InlineKeyboardMarkup(keyboard)

############################# Messages #########################################
def main_menu_message():
   print('message')
   return 'Choose the option in main menu:'

def first_menu_message():
  return 'Choose the submenu in first menu:'

def second_menu_message():
  return 'Choose the submenu in second menu:'

############################# Handlers #########################################
import common
RP = common.load(fname='config.ini')
import credentials as CR
token, Bcast_chatID = CR.get_credentials(RP.token_file)
#U = Updater(token)
U = Updater(token=token, use_context=True)
D = U.dispatcher
J = U.job_queue


# Start
D.add_handler(CommandHandler('start', start))
# Re-Load
D.add_handler(CommandHandler('reload', restart))
# Stop
D.add_handler(CommandHandler('stop', stop))
D.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
#D.add_handler(CallbackQueryHandler(first_menu, pattern='m1'))
#D.add_handler(CallbackQueryHandler(second_menu, pattern='m2'))
#D.add_handler(CallbackQueryHandler(first_submenu, pattern='m1_1'))
#D.add_handler(CallbackQueryHandler(second_submenu, pattern='m2_1'))
# Surface Wind
D.add_handler(CommandHandler('sfcwind', tool.sfcwind, pass_args=True, pass_job_queue=True))
# Hola
D.add_handler(CommandHandler('hola', tool.hola))

U.start_polling()
################################################################################
