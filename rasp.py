#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import common
RP = common.load(fname='config.ini')

import sys
import os
here = os.path.dirname(os.path.realpath(__file__))
import datetime as dt

from telegram import ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton as IlKB
from telegram import InlineKeyboardMarkup
from urllib.request import urlretrieve
import credentials as CR
from random import choice
from threading import Thread
import tool
import aemet
import admin
import channel

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

@CR.restricted
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

@CR.restricted
def restart(update,context):
   """ Reload the Bot to update code, for instance """
   txt = 'Bot is restarting...'
   chatID = update['message']['chat']['id']
   context.bot.send_message(chat_id=chatID, text=txt, 
                            parse_mode=ParseMode.MARKDOWN)
   Thread(target=stop_and_restart).start()

@CR.restricted
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

## Soundings ###################################################################
def sounding_selector(update,context):
   update.message.reply_text(places_message(),
                             reply_markup=places_keyboard())
   context.user_data['main_callback'] = 'main_sfcwind'
   context.user_data['operation'] = 'sounding'
   context.user_data['scalar'] = None
   context.user_data['vector'] = None
   context.user_data['cover']  = None

def map_menu(update,context):
   query = update.callback_query
   context.bot.edit_message_text(chat_id=query.message.chat_id,
                                 message_id=query.message.message_id,
                                 text = places_message(),
                                 reply_markup = places_keyboard())
   context.user_data['operation'] = 'sounding'
   context.user_data['scalar'] = None
   context.user_data['vector'] = None
   context.user_data['cover']  = None


## Menu Options ################################################################
def map_selector(update,context):
   context.user_data['main_callback'] = 'main_map'
   context.user_data['operation'] = 'map'
   context.user_data['scalar'] = None
   context.user_data['vector'] = None
   context.user_data['cover']  = None
   update.message.reply_text(vector_message(),
              reply_markup=vector_keyboard(context.user_data['main_callback']))

def map_menu(update,context):
   query = update.callback_query
   context.bot.edit_message_text(chat_id=query.message.chat_id,
               message_id=query.message.message_id,
               text=vector_message(),
               reply_markup=vector_keyboard(context.user_data['main_callback']))
   context.user_data['main_callback'] = 'main_map'
   context.user_data['operation'] = 'map'
   context.user_data['scalar'] = None
   context.user_data['vector'] = None
   context.user_data['cover']  = None

def keeper(update,context):
   query = update.callback_query
   chatID = query.message.chat_id
   messageID = query.message.message_id
   job_queue = context.job_queue
   data = query['data']
   if data.startswith('vec_'):
      context.user_data['vector'] = query['data'].replace('vec_','')
      txt = scalar_message()
      keyboard = scalar_keyboard()
   elif data.startswith('scal_'):
      context.user_data['scalar'] = query['data'].replace('scal_','')
      txt = day_message()
      keyboard = day_keyboard()
   elif data.startswith('place_'):
      context.user_data['place'] = query['data'].replace('place_','')
      txt = day_message()
      keyboard = day_keyboard()
   elif data.startswith('day_'):
      context.user_data['day'] = query['data'].replace('day_','')
      txt = hour_message()
      if context.user_data['operation'] != 'map': vid=False
      else: vid=True
      keyboard = hour_keyboard(context.user_data['main_callback'],offer_vid=vid)
   elif data.startswith('hour_'):
      context.user_data['hour'] = query['data'].replace('hour_','').split(':')[0]
      txt = finalmessage() + '\n'
      for k,v in context.user_data.items():
         txt += f'  {k}: {v}\n'
      keyboard = None
   elif data == 'stop':
      txt = 'Cancelado!'
      keyboard = None
      context.user_data = {}   # Reset in case of cancel
   if keyboard != None:
      # Continue recolecting data
      context.bot.edit_message_text(chat_id = chatID,
                                    message_id = messageID,
                                    text = txt, reply_markup = keyboard)
   else:
      # Get & send map/plot and finish conversation
      context.bot.edit_message_text(chat_id = chatID,
                                    message_id = messageID,
                                    text = txt)
      # Send picture or do something
      date = dt.datetime.now()
      date = date + dt.timedelta(days=int(context.user_data['day']))
      try:  # video has no defined hour
         date = date.replace(hour=int(context.user_data['hour']))
         date = date.replace(minute=0,second=0,microsecond=0)
      except ValueError:
         date = date.replace(hour=0,minute=0,second=0,microsecond=0)
      if context.user_data['operation'] == 'sounding':
         place = context.user_data['place']
         tool.send_sounding(place,date,context.bot,chatID,job_queue)
      elif context.user_data['operation'] == 'map':
         context.user_data['cover'] = None  #XXX future implementation
         # tool.build_image(date, context.user_data['scalar'],
         tool.decide_image(date, context.user_data['scalar'],
                                 context.user_data['vector'],
                                 context.user_data['cover'],
                                 context.bot,chatID,job_queue)
         context.user_data = {}   # reset after sending??


## Selectors #################################
def selector(update,context,main_callback,operation,scalar,vector,cover):
   context.user_data['main_callback'] = main_callback
   context.user_data['operation'] = operation
   context.user_data['scalar'] = scalar
   context.user_data['vector'] = vector
   context.user_data['cover']  = cover
   update.message.reply_text(day_message(),
                             reply_markup=day_keyboard(main_callback))

def menu(update,context,main_callback,operation,scalar,vector,cover):
   query = update.callback_query
   context.user_data['main_callback'] = main_callback
   context.user_data['operation'] = operation
   context.user_data['scalar'] = scalar
   context.user_data['vector'] = vector
   context.user_data['cover']  = cover
   context.bot.edit_message_text(chat_id=query.message.chat_id,
                                 message_id=query.message.message_id,
                                 text=day_message(),
                                 reply_markup=day_keyboard(main_callback))

## SFCwind
def sfcwind_selector(update,context):
   main_callback = 'main_sfcwind'
   operation = 'map'
   scalar = 'sfcwind'
   vector = 'sfcwind'
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def sfcwind_menu(update,context):
   main_callback = 'main_sfcwind'
   operation = 'map'
   scalar = 'sfcwind'
   vector = 'sfcwind'
   cover  = None
   menu(update,context,main_callback,operation,scalar,vector,cover)


## BLwind
def blwind_selector(update,context):
   main_callback = 'main_blwind'
   operation = 'map'
   scalar = 'blwind'
   vector = 'blwind'
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def blwind_menu(update,context):
   main_callback = 'main_blwind'
   operation = 'map'
   scalar = 'blwind'
   vector = 'blwind'
   cover  = None
   menu(update,context,main_callback,operation,scalar,vector,cover)

## BLTopwind
def bltopwind_selector(update,context):
   main_callback = 'main_bltopwind'
   operation = 'map'
   scalar = 'bltopwind'
   vector = 'bltopwind'
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def bltopwind_menu(update,context):
   main_callback = 'main_bltopwind'
   operation = 'map'
   scalar = 'bltopwind'
   vector = 'bltopwind'
   cover  = None
   menu(update,context,main_callback,operation,scalar,vector,cover)

## Thermals
def thermals_selector(update,context):
   main_callback = 'main_thermals'
   operation = 'map'
   scalar = 'wstar'
   vector = 'sfcwind'
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def thermals_menu(update,context):
   main_callback = 'main_thermals'
   operation = 'map'
   scalar = 'wstar'
   vector = 'sfcwind'
   cover  = None
   menu(update,context,main_callback,operation,scalar,vector,cover)

## Techo
def techo_selector(update,context):
   main_callback = 'main_hglider'
   operation = 'map'
   scalar = 'hglider'
   vector = 'sfcwind'
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def techo_menu(update,context):
   main_callback = 'main_hglider'
   operation = 'map'
   scalar = 'hglider'
   vector = 'sfcwind'
   cover  = None
   menu(update,context,main_callback,operation,scalar,vector,cover)

## Convergencias
def wblmaxmin_selector(update,context):
   main_callback = 'main_wblmaxmin'
   operation = 'map'
   scalar = 'wblmaxmin'
   vector = 'sfcwind'
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def wblmaxmin_menu(update,context):
   main_callback = 'main_wblmaxmin'
   operation = 'map'
   scalar = 'wblmaxmin'
   vector = 'sfcwind'
   cover  = None
   menu(update,context,main_callback,operation,scalar,vector,cover)

############################ Keyboards #########################################
def reset_options(main_callback):
   dummy = [IlKB('Volver a empezar', callback_data=main_callback),
            IlKB('Cancelar', callback_data='stop')]
   return dummy

def vector_keyboard(main_callback='main_map'):
   keyboard = [[IlKB('Superficie', callback_data='vec_sfcwind'),
               IlKB('Promedio', callback_data='vec_blwind'),
               IlKB('Altura', callback_data='vec_bltopwind')],
               [IlKB('Ninguno', callback_data='vec_none')]]
   keyboard.append( reset_options(main_callback) )
   return InlineKeyboardMarkup(keyboard)

def scalar_keyboard(main_callback='main_map'):
   keyboard = [[IlKB('Viento superficie', callback_data='scal_sfcwind'),
                IlKB('Promedio', callback_data='scal_blwind'),
                IlKB('Altura', callback_data='scal_bltopwind')],
               [IlKB('Techo (azul)', callback_data='scal_hglider'),
                IlKB('Base nube', callback_data='scal_zsfclcl')],
               [IlKB('CAPE', callback_data='scal_cape'),
                IlKB('Térmica', callback_data='scal_wstar')],
               [IlKB('Convergencias', callback_data='scal_wblmaxmin'),
                IlKB('Cielo cubierto', callback_data='scal_zblcl')]]
   keyboard.append( reset_options(main_callback) )
   return InlineKeyboardMarkup(keyboard)


def cover_keyboard(main_callback='main_map'):
   keyboard = [[IlKB('Nubes', callback_data='over_blcloudpct'),
                IlKB('Isobaras', callback_data='over_press')],
               [IlKB('None', callback_data='over_none')]]
   keyboard.append( reset_options('main_map') )
   return InlineKeyboardMarkup(keyboard)

def places_keyboard(main_callback='main_map'):
   places = open(here+'/soundings.csv','r').read().strip().splitlines()
   places = dict([l.split(',') for l in places])
   places_keys = list(places.keys())
   keyboard = []
   for i in range(0,len(places_keys),2):
      try:
         P = places_keys[i]
         P1 = places_keys[i+1]
         keyboard.append([IlKB(P.capitalize(), callback_data='place_'+P),
                          IlKB(P1.capitalize(), callback_data='place_'+P1)])
      except IndexError:
         P = places_keys[i]
         keyboard.append([IlKB(P.capitalize(), callback_data=P), ])
   keyboard.append( reset_options('main_map') )
   return InlineKeyboardMarkup(keyboard)

def day_keyboard(main_callback='main_map'):
   keyboard = [[IlKB('Hoy', callback_data='day_0'),
                IlKB('Mañana', callback_data='day_1')],
               [IlKB('Pasado', callback_data='day_2'),
                IlKB('Al otro', callback_data='day_3')]]
   keyboard.append( reset_options(main_callback) )
               # [IlKB('Volver a empezar', callback_data='main'),
               #  IlKB('Cancelar', callback_data='stop')]]
   return InlineKeyboardMarkup(keyboard)

def hour_keyboard(main_callback='main_map',offer_vid=True):
   #XXX local time
   keyboard = [[IlKB("9:00",  callback_data='hour_9:00') ,
                IlKB("10:00", callback_data='hour_10:00'),
                IlKB("11:00", callback_data='hour_11:00'),
                IlKB("12:00", callback_data='hour_12:00')],
               [IlKB("13:00", callback_data='hour_13:00') ,
                IlKB("14:00", callback_data='hour_14:00'),
                IlKB("15:00", callback_data='hour_15:00'),
                IlKB("16:00", callback_data='hour_16:00')],
               [IlKB("17:00", callback_data='hour_17:00') ,
                IlKB("18:00", callback_data='hour_18:00'),
                IlKB("19:00", callback_data='hour_19:00'),
                IlKB("20:00", callback_data='hour_20:00')]]
   if offer_vid: 
      keyboard.append( [IlKB('Todas (video)', callback_data='hour_all')] )
   keyboard.append( reset_options(main_callback) )
                  # [IlKB('Volver a empezar', callback_data='main'),
                  #  IlKB('Cancelar', callback_data='stop')]]
   return InlineKeyboardMarkup(keyboard)


############################# Messages #########################################
def vector_message():
   return 'Flujo de viento:'

def scalar_message():
   return 'Propiedad:'

def cover_message():
   return 'Cobertura:'

def day_message():
   return 'Elige día:'

def hour_message():
   return 'Elige hora:'

def finalmessage():
   return 'Enviando:'

def places_message():
   return 'Elige zona:'

############################# Handlers #########################################
# token, Bcast_chatID = CR.get_credentials('Tester.token')
MB = CR.get_credentials(RP.token_file)
token = MB.token
Bcast_chatID = MB.chatIDs[-1]
U = Updater(token, use_context=True)
D = U.dispatcher
J = U.job_queue

D.add_handler(CommandHandler('map', map_selector))
D.add_handler(CallbackQueryHandler(map_menu, pattern='main_map'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'vec_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'scal_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'over_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'day_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'hour_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'place_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern='stop'))

D.add_handler(CommandHandler('sondeo', sounding_selector))

# Shortcuts
D.add_handler(CommandHandler('sfcwind', sfcwind_selector))
D.add_handler(CallbackQueryHandler(sfcwind_menu, pattern='main_sfcwind'))
D.add_handler(CommandHandler('bltopwind', bltopwind_selector))
D.add_handler(CallbackQueryHandler(bltopwind_menu, pattern='main_bltopwind'))
D.add_handler(CommandHandler('blwind', blwind_selector))
D.add_handler(CallbackQueryHandler(blwind_menu, pattern='main_blwind'))
D.add_handler(CommandHandler('techo', techo_selector))
D.add_handler(CallbackQueryHandler(techo_menu, pattern='main_hglider'))
D.add_handler(CommandHandler('termicas', thermals_selector))
D.add_handler(CallbackQueryHandler(thermals_menu, pattern='main_thermals'))
D.add_handler(CommandHandler('convergencias', wblmaxmin_selector))
D.add_handler(CallbackQueryHandler(wblmaxmin_menu, pattern='main_wblmaxmin'))

# Admin
D.add_handler(CommandHandler('start', start))
D.add_handler(CommandHandler('stop', stop))
D.add_handler(CommandHandler('reload', restart))
D.add_handler(CommandHandler('stats', stats))
D.add_handler(CommandHandler('hola', tool.hola))
D.add_handler(CommandHandler('help', tool.myhelp))

## Setup DB for files ##########################################################
admin.create_db(RP.DBname)

# Broadcast
J.run_daily(channel.broadcast, dt.time(8,30), context=(Bcast_chatID,))
# J.run_daily(channel.close_poll, dt.time(23,50), context=(Bcast_chatID,)) 

U.start_polling()
################################################################################
