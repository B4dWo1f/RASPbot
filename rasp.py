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
from telegram.ext import MessageHandler, Filters
# My Libraies
import credentials as CR
import menus as M
import channel
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
   txt = 'Hola!\n'
   txt += 'Para ver los comandos disponibles: /help\n'
   txt += 'A día de hoy esta son las opciones disponibles:\n'
   txt += tool.help_txt()
   txt += '\n\nActualizaciones y noticias de este bot:\n'
   txt += 'https://t.me/parapentebotWiki'
   context.bot.send_message(chat_id=update.message.chat_id, text=txt,
                            disable_web_page_preview=True)
   conn,c = admin.connect(RP.DBname)
   ad_lv = min([usr[-2] for usr in admin.get_user(conn,'chatid',chatID)])
   admin_level = min([admin_level,ad_lv])
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

# Custom map
D.add_handler(CommandHandler('map', M.map_selector))
D.add_handler(CallbackQueryHandler(M.map_menu, pattern='main_map'))

# Conversation-like handlers
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'aemet_([\w*])'))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'oper_([\w*])'))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'place_([\w*])', pass_user_data=True))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'vec_([\w*])'))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'scal_([\w*])'))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'over_([\w*])'))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'day_([\w*])'))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern=r'hour_([\w*])'))
D.add_handler(CallbackQueryHandler(M.options_handler, pattern='stop'))

# Sondeo
D.add_handler(CommandHandler('sondeo', M.sounding_selector))
D.add_handler(CallbackQueryHandler(M.sounding_menu, pattern='main_sounding'))

# Shortcuts
D.add_handler(CommandHandler('sfcwind', M.sfcwind_selector))
D.add_handler(CallbackQueryHandler(M.sfcwind_menu, pattern='main_sfcwind'))
D.add_handler(CommandHandler('bltopwind', M.bltopwind_selector))
D.add_handler(CallbackQueryHandler(M.bltopwind_menu, pattern='main_bltopwind'))
D.add_handler(CommandHandler('blwind', M.blwind_selector))
D.add_handler(CallbackQueryHandler(M.blwind_menu, pattern='main_blwind'))
D.add_handler(CommandHandler('techo', M.techo_selector))
D.add_handler(CallbackQueryHandler(M.techo_menu, pattern='main_hglider'))
D.add_handler(CommandHandler('base_nube', M.cumulos_selector))
D.add_handler(CallbackQueryHandler(M.cumulos_menu, pattern='main_zsfclcl'))
D.add_handler(CommandHandler('cubierta_nube', M.overcast_selector))
D.add_handler(CallbackQueryHandler(M.overcast_menu, pattern='main_zblcl'))
D.add_handler(CommandHandler('termicas', M.thermals_selector))
D.add_handler(CallbackQueryHandler(M.thermals_menu, pattern='main_thermals'))
D.add_handler(CommandHandler('convergencias', M.wblmaxmin_selector))
D.add_handler(CallbackQueryHandler(M.wblmaxmin_menu, pattern='main_wblmaxmin'))
D.add_handler(CommandHandler('lluvia', M.rain_selector))
D.add_handler(CallbackQueryHandler(M.rain_menu, pattern='main_rain'))


# ## TESTING meteograma
# D.add_handler(CommandHandler('meteograma', M.meteogram_selector))
# D.add_handler(CallbackQueryHandler(M.meteogram_menu, pattern='main_meteogram'))
# D.add_handler(MessageHandler(Filters.location, M.localization_callback, pass_user_data=True))


# Aemet
D.add_handler(CommandHandler('aemet', M.aemet_selector))
D.add_handler(CallbackQueryHandler(M.aemet_menu, pattern='main_aemet'))

# Admin
D.add_handler(CommandHandler('start', start))
D.add_handler(CommandHandler('stop', stop))
D.add_handler(CommandHandler('reload', restart))
D.add_handler(CommandHandler('stats', stats))
D.add_handler(CommandHandler('hola', tool.hola))
D.add_handler(CommandHandler('help', tool.myhelp))
D.add_handler(CommandHandler('log', tool.log))
D.add_handler(CommandHandler('feedback', tool.feedback))

## Setup DB for files ##########################################################
admin.create_db(RP.DBname)

# Broadcast
J.run_daily(channel.broadcast, dt.time(8,30), context=(Bcast_chatID,))

U.start_polling()
################################################################################
