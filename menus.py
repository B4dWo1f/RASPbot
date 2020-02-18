#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import datetime as dt
from telegram import InlineKeyboardButton as IlKB
from telegram import InlineKeyboardMarkup
import tool
import os
here = os.path.dirname(os.path.realpath(__file__))

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
      if context.user_data['operation'] != 'rain': warn = False
      else: warn = True
      txt = hour_message(warn)
      if context.user_data['operation'] != 'map': vid=False
      else: vid=True
      keyboard = hour_keyboard(context.user_data['main_callback'],offer_vid=vid)
   elif data.startswith('hour_'):
      context.user_data['hour'] = query['data'].replace('hour_','').split(':')[0]
      txt = finalmessage() + '\n'
      for k,v in context.user_data.items():
         if k in ['day','hour','scalar','vector']:
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
      elif context.user_data['operation'] == 'rain':
         tool.send_rain(date,context.bot,chatID,job_queue)



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

## Cloud
def nube_selector(update,context):
   main_callback = 'main_zsfclcl'
   operation = 'map'
   scalar = 'zsfclcl'
   vector = 'sfcwind'
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def nube_menu(update,context):
   main_callback = 'main_zsfclcl'
   operation = 'map'
   scalar = 'zsfclcl'
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

## Rain
def rain_selector(update,context):
   main_callback = 'main_rain'
   operation = 'rain'
   scalar = None
   vector = None
   cover  = None
   selector(update,context,main_callback,operation,scalar,vector,cover)

def rain_menu(update,context):
   main_callback = 'main_rain'
   operation = 'map'
   scalar = None
   vector = None
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

def hour_message(warn=False):
   if warn:
      return 'Elige hora:\n(puede que no todas las horas estén disponibles)'
   else: return 'Elige hora:'

def finalmessage():
   return 'Enviando:'

def places_message():
   return 'Elige zona:'

