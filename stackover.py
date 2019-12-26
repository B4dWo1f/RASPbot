#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
here = os.path.dirname(os.path.realpath(__file__))
import datetime as dt

from telegram import ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from urllib.request import urlretrieve
import credentials as CR
from random import choice
import tool
import aemet

def sounding_selector(update,context):
   update.message.reply_text(places_message(),
                             reply_markup=places_keyboard())
   context.user_data['operation'] = 'sounding'

def map_menu(update,context):
   query = update.callback_query
   context.bot.edit_message_text(chat_id=query.message.chat_id,
                                 message_id=query.message.message_id,
                                 text = places_message(),
                                 reply_markup = places_keyboard())
   context.user_data['operation'] = 'sounding'

def send_sounding(place,date,bot,chatID,job_queue):
   places = {'arcones': 1, 'bustarviejo': 2, 'cebreros': 3, 'abantos': 4,
             'piedrahita': 5, 'pedro bernardo': 6, 'lillo': 7,
             'fuentemilanos': 8, 'candelario': 10, 'pitolero': 11,
             'pegalajar': 12, 'otivar': 13}
   print('**************')
   print(place)
   print(date)
   print('**************')
   fol,_ = tool.locate(date,'')
   print('==>',fol)
   index = places[place]
   H = date.strftime('%H%M')
   url_picture = 'http://raspuri.mooo.com/RASP/'
   url_picture += f'{fol}/FCST/sounding{index}.curr.{H}lst.w2.png'
   print(url_picture)
   f_tmp = '/tmp/' + tool.rand_name() + '.png'
   urlretrieve(url_picture, f_tmp)
   T = aemet.get_temp(place,date)
   txt = "Sounding for _%s_ at %s"%(place.capitalize(), date.strftime('%d/%m/%Y-%H:%M'))
   if T != None:
      txt += '\nExpected temperature: *%s°C*'%(T)
   print(txt)
   ##tool.send_media(update,context, f_tmp, msg=txt, t=180,delete=True)
   tool.send_media(bot,chatID,job_queue, f_tmp, caption=txt,
                                         t_del=5*60, t_renew=6*60*60,
                                         dis_notif=False)
   os.system(f'rm {f_tmp}')
   return

############################### Bot ############################################
def map_selector(update,context):
   update.message.reply_text(vector_message(),
                             reply_markup=vector_keyboard())
   context.user_data['operation'] = 'map'

def map_menu(update,context):
   query = update.callback_query
   context.bot.edit_message_text(chat_id=query.message.chat_id,
                                 message_id=query.message.message_id,
                                 text=vector_message(),
                                 reply_markup=vector_keyboard())
   context.user_data['operation'] = 'map'

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
      txt = cover_message()
      keyboard = cover_keyboard()
   elif data.startswith('over_'):
      context.user_data['over'] = query['data'].replace('over_','')
      txt = day_message()
      keyboard = day_keyboard()
   elif data.startswith('place_'):
      context.user_data['place'] = query['data'].replace('place_','')
      txt = day_message()
      keyboard = day_keyboard()
   elif data.startswith('day_'):
      context.user_data['day'] = query['data'].replace('day_','')
      txt = hour_message()
      keyboard = hour_keyboard()
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
      date = date.replace(hour=int(context.user_data['hour']))
      date = date.replace(minute=0,second=0,microsecond=0)
      if context.user_data['operation'] == 'sounding':
         place = context.user_data['place']
         send_sounding(place,date,context.bot,chatID,job_queue)
      elif context.user_data['operation'] == 'map':
         print('HEREEEE')
         tool.build_image(date,context.user_data['scalar'],context.user_data['vector'], context.bot,chatID,job_queue)
      # context.user_data = {}   # reset after sending??


############################ Keyboards #########################################
def vector_keyboard():
   keyboard = [[InlineKeyboardButton('Superficie', callback_data='vec_sfcwind'),
               InlineKeyboardButton('Media Altura', callback_data='vec_blwind'),
               InlineKeyboardButton('Altura', callback_data='vec_bltopwind')],
               [InlineKeyboardButton('Ninguno', callback_data='vec_none')]]
   return InlineKeyboardMarkup(keyboard)

def scalar_keyboard():
   keyboard = [[InlineKeyboardButton('Viento superficie', callback_data='scal_sfcwind'),
                InlineKeyboardButton('Media altura', callback_data='scal_blwind'),
                InlineKeyboardButton('Altura', callback_data='scal_bltopwind')],
               [InlineKeyboardButton('Altura capa convectiva', callback_data='scal_hbl'),
                InlineKeyboardButton('Altura térmicas', callback_data='scal_hglider'),
                InlineKeyboardButton('Potencia térmicas', callback_data='scal_wstar')],
               [InlineKeyboardButton('CAPE', callback_data='scal_cape')],
               [InlineKeyboardButton('B/S ratio', callback_data='scal_bsratio'),
                InlineKeyboardButton('bl max u/d motion', callback_data='scal_wblmaxmin')],
               [InlineKeyboardButton('Volver a empezar', callback_data='main'),
                InlineKeyboardButton('Cancelar', callback_data='stop')]]
   return InlineKeyboardMarkup(keyboard)

def cover_keyboard():
   keyboard = [[InlineKeyboardButton('Nubes', callback_data='over_blcloudpct'),
                InlineKeyboardButton('Isobaras', callback_data='over_press')],
               [InlineKeyboardButton('None', callback_data='over_none')],
               [InlineKeyboardButton('Volver a empezar', callback_data='main'),
                InlineKeyboardButton('Cancelar', callback_data='stop')]]
   return InlineKeyboardMarkup(keyboard)

def places_keyboard():
   places = open(here+'/soundings.csv','r').read().strip().splitlines()
   places = dict([l.split(',') for l in places])
   places_keys = list(places.keys())
   keyboard = []
   for i in range(0,len(places_keys),2):
      try:
         P = places_keys[i]
         P1 = places_keys[i+1]
         keyboard.append([InlineKeyboardButton(P.capitalize(), callback_data='place_'+P),
                          InlineKeyboardButton(P1.capitalize(), callback_data='place_'+P1)])
      except IndexError:
         P = places_keys[i]
         keyboard.append([IlKB(P.capitalize(), callback_data=P), ])
   return InlineKeyboardMarkup(keyboard)

def day_keyboard():
   keyboard = [[InlineKeyboardButton('Hoy', callback_data='day_0'),
                InlineKeyboardButton('Mañana', callback_data='day_1')],
               [InlineKeyboardButton('Pasado', callback_data='day_2'),
                InlineKeyboardButton('Al otro', callback_data='day_3')],
               [InlineKeyboardButton('Volver a empezar', callback_data='main'),
                InlineKeyboardButton('Cancelar', callback_data='stop')]]
   return InlineKeyboardMarkup(keyboard)

def hour_keyboard():
   keyboard = [[InlineKeyboardButton("9:00",  callback_data='hour_9:00') ,
                InlineKeyboardButton("10:00", callback_data='hour_10:00'),
                InlineKeyboardButton("11:00", callback_data='hour_11:00'),
                InlineKeyboardButton("12:00", callback_data='hour_12:00')],
               [InlineKeyboardButton("13:00", callback_data='hour_13:00') ,
                InlineKeyboardButton("14:00", callback_data='hour_14:00'),
                InlineKeyboardButton("15:00", callback_data='hour_15:00'),
                InlineKeyboardButton("16:00", callback_data='hour_16:00')],
               [InlineKeyboardButton("17:00", callback_data='hour_17:00') ,
                InlineKeyboardButton("18:00", callback_data='hour_18:00'),
                InlineKeyboardButton("19:00", callback_data='hour_19:00'),
                InlineKeyboardButton("20:00", callback_data='hour_20:00')],
               [InlineKeyboardButton('Volver a empezar', callback_data='main'),
                InlineKeyboardButton('Cancelar', callback_data='stop')]]
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
   return 'You have selected:'

def places_message():
   return 'Elige zona:'

def hola(update, context):
   """ echo-like service to check system status """
   # LG.info('Hola!')
   try: chatID = update['message']['chat']['id']
   except TypeError: chatID = update['callback_query']['message']['chat']['id']
   salu2 = ['What\'s up?', 'Oh, hi there!', 'How you doin\'?', 'Hello!']
   txt = choice(salu2)
   M = context.bot.send_message(chatID, text=txt, 
                                parse_mode=ParseMode.MARKDOWN)

############################# Handlers #########################################
token, Bcast_chatID = CR.get_credentials('Tester.token')
U = Updater(token, use_context=True)
D = U.dispatcher

D.add_handler(CommandHandler('map', map_selector))
D.add_handler(CallbackQueryHandler(map_menu, pattern='main'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'vec_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'scal_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'over_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'day_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'hour_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern=r'place_([\w*])'))
D.add_handler(CallbackQueryHandler(keeper, pattern='stop'))

D.add_handler(CommandHandler('sounding', sounding_selector))

D.add_handler(CommandHandler('hola', hola))

U.start_polling()
################################################################################
