#!/usr/bin/python3
# -*- coding: UTF-8 -*-

# Common
import common
import os
here = os.path.dirname(os.path.realpath(__file__))
RP = common.load(fname='config.ini')
   
# Telegram
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
# My Libraies
import credentials as CR
import channel
import menus   
import admin
import tool
# Standard
import sys
import datetime as dt
from threading import Thread
# Log   
import logging
logging.basicConfig(level=RP.log_lv,
                    format='%(asctime)s %(name)s:%(levelname)s - %(message)s',
                    datefmt='%Y/%m/%d-%H:%M:%S',
                    filename=RP.log, filemode='w')
LG = logging.getLogger('main')


## Bot-Admin ###################################################################
# Start
def start(update, context):
   """ Welcome message and user registration """
   ch = update.message.chat
   chatID = ch.id
   uname = ch.username
   fname = ch.first_name
   lname = ch.last_name
   if ch.id in CR.ADMINS_id: admin_level = 0
   else: admin_level = 3
   txt = "I'm a bot, please talk to me!"
   context.bot.send_message(chat_id=update.message.chat_id, text=txt)
   conn,c = admin.connect(RP.DBname)
   admin.insert_user(conn,chatID,uname,fname,lname,admin_level,0)

# Stop
def shutdown():
   U.stop()
   U.is_idle = False

@CR.restricted(0)
def stop(update, context):
   """ Completely halt the Bot """
   chatID = update['message']['chat']['id']
   txt = 'I\'ll be shutting down\nI hope to see you soon!'
   context.bot.send_message(chatID, text=txt, parse_mode=ParseMode.MARKDOWN)
   Thread(target=shutdown).start()

# Reload
def stop_and_restart():
   """
   Gracefully stop the Updater and replace the current process with a new one
   """
   U.stop()
   os.execl(sys.executable, sys.executable, *sys.argv)

@CR.restricted(0)
def restart(update,context):
   """ Reload the Bot to update code, for instance """
   txt = 'Bot is restarting...'
   chatID = update['message']['chat']['id']
   context.bot.send_message(chat_id=chatID, text=txt, 
                            parse_mode=ParseMode.MARKDOWN)
   Thread(target=stop_and_restart).start()

@CR.restricted(0)
def stats(update,context):
   def format_stats(header,lines):
      lens = [10,5,5]
      chatid,uname,fname,lname,admin,usage = header.split()
      header = [fname.ljust(10)[:10],
                admin.ljust(5)[:5],
                usage.ljust(5)[:5]]
      header = ' '.join(header)
      fmt_lines = []
      for l in lines:
         ll = l.split()
         fname = ll[2].ljust(10)[:10]
         adm_lv = ll[-2].ljust(5)[:5]
         usage = ll[-1].ljust(5)[:5]
         fmt_lines.append(' '.join([fname,adm_lv,usage]))
      return '\n'.join([header] + fmt_lines)
   conn,c = admin.connect(RP.DBname)
   usage = admin.show_all(conn,'users').splitlines()
   header = usage[0]
   txt = format_stats(header, usage[1:])
   txt = f'`{txt}`'
   chatID = update['message']['chat']['id']
   context.bot.send_message(chat_id=chatID, text=txt, 
                            parse_mode=ParseMode.MARKDOWN)

############################# Handlers #########################################
# token, Bcast_chatID = CR.get_credentials('Tester.token')
MB = CR.get_credentials(RP.token_file)
token = MB.token
admin_chatID = MB.chatIDs[-1]
Bcast_chatID = MB.chatIDs[-1]
U = Updater(token, use_context=True)
D = U.dispatcher
J = U.job_queue

D.add_handler(CommandHandler('map', menus.map_selector))
D.add_handler(CallbackQueryHandler(menus.map_menu, pattern='main_map'))
D.add_handler(CallbackQueryHandler(menus.keeper, pattern=r'vec_([\w*])'))
D.add_handler(CallbackQueryHandler(menus.keeper, pattern=r'scal_([\w*])'))
D.add_handler(CallbackQueryHandler(menus.keeper, pattern=r'over_([\w*])'))
D.add_handler(CallbackQueryHandler(menus.keeper, pattern=r'day_([\w*])'))
D.add_handler(CallbackQueryHandler(menus.keeper, pattern=r'hour_([\w*])'))
D.add_handler(CallbackQueryHandler(menus.keeper, pattern=r'place_([\w*])'))
D.add_handler(CallbackQueryHandler(menus.keeper, pattern='stop'))

D.add_handler(CommandHandler('sondeo', menus.sounding_selector))

# Shortcuts
D.add_handler(CommandHandler('sfcwind', menus.sfcwind_selector))
D.add_handler(CallbackQueryHandler(menus.sfcwind_menu, pattern='main_sfcwind'))
D.add_handler(CommandHandler('bltopwind', menus.bltopwind_selector))
D.add_handler(CallbackQueryHandler(menus.bltopwind_menu, pattern='main_bltopwind'))
D.add_handler(CommandHandler('blwind', menus.blwind_selector))
D.add_handler(CallbackQueryHandler(menus.blwind_menu, pattern='main_blwind'))
D.add_handler(CommandHandler('techo', menus.techo_selector))
D.add_handler(CallbackQueryHandler(menus.techo_menu, pattern='main_hglider'))
D.add_handler(CommandHandler('termicas', menus.thermals_selector))
D.add_handler(CallbackQueryHandler(menus.thermals_menu, pattern='main_thermals'))
D.add_handler(CommandHandler('convergencias', menus.wblmaxmin_selector))
D.add_handler(CallbackQueryHandler(menus.wblmaxmin_menu, pattern='main_wblmaxmin'))
D.add_handler(CommandHandler('lluvia', menus.rain_selector))
D.add_handler(CallbackQueryHandler(menus.rain_menu, pattern='main_rain'))

# Admin
D.add_handler(CommandHandler('start', start))
D.add_handler(CommandHandler('stop', stop))
D.add_handler(CommandHandler('reload', restart))
D.add_handler(CommandHandler('stats', stats))
D.add_handler(CommandHandler('hola', tool.hola))
D.add_handler(CommandHandler('help', tool.myhelp))
D.add_handler(CommandHandler('log', tool.log))

## Setup DB for files ##########################################################
admin.create_db(RP.DBname)

# Broadcast
J.run_daily(channel.broadcast, dt.time(8,30), context=(Bcast_chatID,))

U.start_polling()
################################################################################
