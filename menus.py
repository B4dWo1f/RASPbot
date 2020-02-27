#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import datetime as dt
import keyboards as kb
import tool


def options_handler(update,context):
   """
   This function will ask and guide the user through any available options
   I define a options cascades:
   /aemet -> operation -> day -> hour(vid=False)
   /sondeo -> place -> day -> hour(vid=True)
   /map -> day -> hour(vid=False)
   /[shortcuts] -> day -> hour(vid=True)
   /meteogram -> place -> day

   In order to fully define the requested operation we need to store in 
   context.user_data the following information:
   - main_callback: property to return to the beginning of the cascade
   - operation: aemet, map, sounding, meteogram
   - oper_class: type of operation [for aemet: cloud&rain, for map: custom,
                                                                    shortcut...]
   - place: None, [takeoffs], personal
   - day: 0, 1, 2, 3 [today, tomorrow,...]
   - hour: 8,9,...20 [available forecasts in Spanish Local time]
   - scalar: sfcwind, hglider... [the available RASP properties]
   - vector: sfcwind, blwind... [the available RASP wind options]
   - cover: unavailable for now. Future implementation
   """
   query = update.callback_query
   job_queue = context.job_queue
   # Try-catch to allow the possibility of arriving here just by sending the
   # location
   try:
      chatID = update['message']['chat']['id']
      messageID = update['message']['message_id']
   except TypeError:
      chatID = update['callback_query']['message']['chat']['id']
      messageID = update['callback_query']['message']['message_id']
   # User passed data
   try: data = query['data']
   except TypeError: data = 'personal'  # when location sent
   ### Options cascades ###
   if data.startswith('place_'):
      context.user_data['place'] = query['data'].replace('place_','')
      txt = kb.day_msg()
      keyboard = kb.day(context.user_data['main_callback'])
   elif data.startswith('day_'):
      context.user_data['day'] = query['data'].replace('day_','')
      if context.user_data['operation'] == 'meteogram':
         txt = finalmessage()
         keyboard = None
      else:
         if context.user_data['operation'] == 'aemet': warn = True
         else: warn = False
         txt = kb.hour_msg(warn)
         if context.user_data['operation'] == 'shortcut': vid=True
         elif context.user_data['operation'] == 'sounding': vid=True
         elif context.user_data['operation'] == 'map': vid=False
         elif context.user_data['operation'] == 'rain': vid = False  #XXX check
         else: vid=False
         keyboard = kb.hour(context.user_data['main_callback'],offer_vid=vid)
   elif data.startswith('hour_'):
      context.user_data['hour'] = query['data'].replace('hour_','').split(':')[0]
      txt = kb.finalmsg() + '\n'
      for k,v in context.user_data.items():
         if k in ['day','hour','scalar','vector']:
            txt += f'  {k}: {v}\n'
      keyboard = None
   elif data.startswith('vec_'):
      context.user_data['vector'] = query['data'].replace('vec_','')
      txt = kb.scalar_msg()
      keyboard = kb.scalar(context.user_data['main_callback'])
   elif data.startswith('scal_'):
      context.user_data['scalar'] = query['data'].replace('scal_','')
      txt = kb.day_msg()
      keyboard = kb.day(context.user_data['main_callback'])
   elif data.startswith('aemet_'):
      context.user_data['oper_class'] = query['data'].replace('aemet_','')
      txt = kb.day_msg(warn=True)
      keyboard = kb.day(context.user_data['main_callback'])
   elif data == 'stop':  #XXX error
      txt = 'Cancelado!'
      keyboard = None
      context.user_data = {}   # Reset in case of cancel
   ### Cascades ##
   if keyboard != None:
      # Continue recolecting data
      context.bot.edit_message_text(chat_id = chatID,
                                    message_id = messageID,
                                    text = txt, reply_markup = keyboard)
   else:  # keybard == None means we are done with the cascades
          # and proceed with the petition
      # End the conversation and send info
      context.bot.edit_message_text(chat_id = chatID,
                                    message_id = messageID,
                                    text = txt)
      # Fix day
      # if context.user_data['hour'] == all, date should be reduced to dt.date
      date = dt.datetime.now()
      date = date.replace(minute=0,second=0,microsecond=0)
      date = date + dt.timedelta(days=int(context.user_data['day']))
      if context.user_data['hour'] == 'all':
         date = date.date()
      else: date = date.replace(hour=int(context.user_data['hour']))
      if context.user_data['operation'] == 'sounding':
         place = context.user_data['place']
         tool.send_sounding(place,date,context.bot,chatID,job_queue)
   # elif context.user_data['operation'] == 'meteogram':
   #    print('*************************')
   #    print('yay')
   #    tool.meteogram(date,context.user_data,context.bot,chatID,job_queue)
   #    print('*************************')
      elif context.user_data['operation'] in ['map','shortcut']:
         context.user_data['cover'] = None  #XXX future implementation
         # tool.build_image(date, context.user_data['scalar'],
         tool.decide_image(date, context.user_data['scalar'],
                                 context.user_data['vector'],
                                 context.user_data['cover'],
                                 context.bot,chatID,job_queue)
         context.user_data = {}   # reset after sending??
      elif context.user_data['operation'] == 'aemet':
         oper = context.user_data['oper_class']
         tool.send_aemet(date,oper,context.bot,chatID,job_queue)


## Handlers and Menus ###########################################################
## Selectors #################################
def selector(update,context, main_callback=None,
                             operation=None, oper_class=None,
                             scalar=None, vector=None, cover=None,
                             day=None, hour=None,
                             msg=None, keyboard=None):
   context.user_data['main_callback'] = main_callback
   context.user_data['operation'] = operation
   context.user_data['oper_class'] = operation
   context.user_data['scalar'] = scalar
   context.user_data['vector'] = vector
   context.user_data['cover']  = cover
   context.user_data['day']  = day
   context.user_data['hour']  = hour
   update.message.reply_text(msg,reply_markup=keyboard)

def menu(update,context, main_callback=None,
                         operation=None, oper_class=None,
                         scalar=None, vector=None, cover=None,
                         day=None, hour=None,
                         msg=None, keyboard=None):
   query = update.callback_query
   chatID = query.message.chat_id
   msgID = query.message.message_id
   context.user_data['main_callback'] = main_callback
   context.user_data['operation'] = operation
   context.user_data['oper_class'] = operation
   context.user_data['scalar'] = scalar
   context.user_data['vector'] = vector
   context.user_data['cover']  = cover
   context.user_data['day']  = day
   context.user_data['hour']  = hour
   context.bot.edit_message_text(chat_id=chatID, message_id=msgID,
                                 text=msg, reply_markup=keyboard)

# Soundings
def sounding_selector(update,context):
   main_callback = 'main_sounding'
   operation = 'sounding'
   msg = kb.places_msg()
   keyboard = kb.places(main_callback, False,False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            msg=msg, keyboard=keyboard)

def sounding_menu(update,context):
   """
   You should only arrive here from the "start over" option
   """
   main_callback = 'main_sounding'
   operation = 'sounding'
   msg = kb.places_msg()
   keyboard = kb.places(main_callback, False,False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        msg=msg, keyboard=keyboard)


# Custom map
def map_selector(update,context):
   main_callback = 'main_map'
   operation = 'map'
   msg = kb.vector_msg()
   keyboard = kb.vector(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            msg=msg, keyboard=keyboard)

def map_menu(update,context):
   main_callback = 'main_map'
   operation = 'map'
   msg = kb.vector_msg()
   keyboard = kb.vector(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        msg=msg, keyboard=keyboard)

# SFCwind
def sfcwind_selector(update,context):
   main_callback = 'main_sfcwind'
   operation = 'shortcut'
   scalar = 'sfcwind'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def sfcwind_menu(update,context):
   main_callback = 'main_sfcwind'
   operation = 'shortcut'
   scalar = 'sfcwind'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

# BLwind
def blwind_selector(update,context):
   main_callback = 'main_blwind'
   operation = 'shortcut'
   scalar = 'blwind'
   vector = 'blwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def blwind_menu(update,context):
   main_callback = 'main_blwind'
   operation = 'shortcut'
   scalar = 'blwind'
   vector = 'blwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

# BLTopwind
def bltopwind_selector(update,context):
   main_callback = 'main_bltopwind'
   operation = 'shortcut'
   scalar = 'bltopwind'
   vector = 'bltopwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def bltopwind_menu(update,context):
   main_callback = 'main_bltopwind'
   operation = 'shortcut'
   scalar = 'bltopwind'
   vector = 'bltopwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

# Thermals
def thermals_selector(update,context):
   main_callback = 'main_thermals'
   operation = 'shortcut'
   scalar = 'wstar'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def thermals_menu(update,context):
   main_callback = 'main_thermals'
   operation = 'shortcut'
   scalar = 'wstar'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

# Techo
def techo_selector(update,context):
   main_callback = 'main_hglider'
   operation = 'shortcut'
   scalar = 'hglider'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def techo_menu(update,context):
   main_callback = 'main_hglider'
   operation = 'shortcut'
   scalar = 'hglider'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

# Convergencias
def wblmaxmin_selector(update,context):
   main_callback = 'main_wblmaxmin'
   operation = 'shortcut'
   scalar = 'wblmaxmin'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def wblmaxmin_menu(update,context):
   main_callback = 'main_wblmaxmin'
   operation = 'shortcut'
   scalar = 'wblmaxmin'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

## Cloud
def cumulos_selector(update,context):
   main_callback = 'main_zsfclcl'
   operation = 'shortcut'
   scalar = 'zsfclcl'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def cumulos_menu(update,context):
   main_callback = 'main_zsfclcl'
   operation = 'shortcut'
   scalar = 'zsfclcl'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)


## Overcast
def overcast_selector(update,context):
   main_callback = 'main_zblcl'
   operation = 'shortcut'
   scalar = 'zblcl'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def overcast_menu(update,context):
   main_callback = 'main_zblcl'
   operation = 'shortcut'
   scalar = 'zblcl'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

# Rain
def rain_selector(update,context):
   main_callback = 'main_rain'
   operation = 'shortcut'
   scalar = 'rain1'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            scalar=scalar, vector=vector,
                            msg=msg, keyboard=keyboard)

def rain_menu(update,context):
   main_callback = 'main_rain'
   operation = 'shortcut'
   scalar = 'rain1'
   vector = 'sfcwind'
   msg = kb.day_msg()
   keyboard = kb.day(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        scalar=scalar, vector=vector,
                        msg=msg, keyboard=keyboard)

# Aemet
def aemet_selector(update,context):
   main_callback = 'main_aemet'
   operation = 'aemet'
   msg = kb.aemet_msg()
   keyboard = kb.aemet(main_callback, False)
   selector(update,context, main_callback=main_callback, operation=operation,
                            msg=msg, keyboard=keyboard)

def aemet_menu(update,context):
   main_callback = 'main_aemet'
   operation = 'aemet'
   msg = kb.aemet_msg()
   keyboard = kb.aemet(main_callback, False)
   menu(update,context, main_callback=main_callback, operation=operation,
                        msg=msg, keyboard=keyboard)




# def localization_callback(update,context):
#    loc = update['message']['location']
#    lat = loc['latitude']
#    lon = loc['longitude']
#    context.user_data['place'] = (lon,lat)
#    try: chatID = update['message']['chat']['id']
#    except TypeError: chatID = update['callback_query']['message']['chat']['id']
#    messageID = update.message.message_id
#    txt = "Recibida tu ubicación. ¿Qué quieres hacer ahora?"
#    keyboard = loc_keyboard((lon,lat))
#    M = context.bot.send_message(chatID, text=txt,reply_markup=keyboard)
#    # context.user_data['operation'] = 'meteogram'




# ## Meteogram
# def meteogram_selector(update,context):
#    main_callback = 'main_meteogram'
#    context.user_data['main_callback'] = main_callback
#    context.user_data['operation'] = 'meteogram'
#    update.message.reply_text(places_message(),
#                              reply_markup=places_keyboard(main_callback))

# def meteogram_menu(update,context):
#    query = update.callback_query
#    main_callback = 'main_meteogram'
#    context.user_data['main_callback'] = main_callback
#    context.user_data['operation'] = 'meteogram'
#    context.bot.edit_message_text(chat_id=query.message.chat_id,
#                                  message_id=query.message.message_id,
#                                  text=places_message(),
#                                  reply_markup=places_keyboard(main_callback))


