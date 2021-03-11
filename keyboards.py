#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import pandas as pd
from telegram import InlineKeyboardButton as IlKB
# from telegram import KeyboardButton
from telegram import InlineKeyboardMarkup #, ReplyKeyboardMarkup
here = os.path.dirname(os.path.realpath(__file__))

############################ Keyboards #########################################
def reset_options(main_callback=None,restart=True):
   dummy = []
   if restart:
      dummy.append( IlKB('Volver a empezar', callback_data=main_callback) )
   dummy.append(IlKB('Cancelar', callback_data='stop'))
   return dummy

def vector(main_callback,restart=False):
   keyboard = [[IlKB('Superficie', callback_data='vec_sfcwind'),
               IlKB('Promedio', callback_data='vec_blwind'),
               IlKB('Altura', callback_data='vec_bltopwind')],
               [IlKB('Ninguno', callback_data='vec_none')]]
   keyboard.append( reset_options(main_callback,restart=restart) )
   return InlineKeyboardMarkup(keyboard)

def scalar(main_callback,restart=True):
   keyboard = [[IlKB('Viento superficie', callback_data='scal_sfcwind'),
                IlKB('Promedio', callback_data='scal_blwind'),
                IlKB('Altura', callback_data='scal_bltopwind')],
               [IlKB('Techo (azul)', callback_data='scal_hglider'),
                IlKB('Base nube', callback_data='scal_zsfclcl')],
               [IlKB('CAPE', callback_data='scal_cape'),
                IlKB('Térmica', callback_data='scal_wstar')],
               [IlKB('Convergencias', callback_data='scal_wblmaxmin'),
                IlKB('Cielo cubierto', callback_data='scal_zblcl')]]
   keyboard.append( reset_options(main_callback,restart=restart) )
   return InlineKeyboardMarkup(keyboard)


def cover(main_callback):
   keyboard = [[IlKB('Nubes', callback_data='over_blcloudpct'),
                IlKB('Isobaras', callback_data='over_press')],
               [IlKB('None', callback_data='over_none')]]
   keyboard.append( reset_options(main_callback) )
   return InlineKeyboardMarkup(keyboard)

def personal_places(main_callback,personal=True):
   location_keyboard = KeyboardButton(text="Enviar Ubicación",
                                               request_location=True)
   custom_keyboard = [[ location_keyboard ]]
   return ReplyKeyboardMarkup(custom_keyboard)

def places(main_callback,restart=False,personal=True):
   """
   Keyboard with in-line-buttons to select the place of interest.
   if it's the first menu offered, restart = False (since this would be the
   initial step).
   personal: to offer the option of sending a custom geo-position
   * all the returned callback_data should start with "place_"
   """
   # Build buttons upon available soundings
   places_df = pd.read_csv(here+'/soundings1.csv', delimiter=';', header=0)
   if main_callback == 'main_sounding':
      places = places_df[['label','sounding_index']].dropna()
      places = dict(zip(places['label'],map(int,places['sounding_index'])))
   elif main_callback == 'main_meteogram':
      places = places_df[['label','meteogram']].dropna()
      places = dict(zip(places['label'],places['meteogram']))
   else:   # Fallback. to be deleted
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
         keyboard.append([IlKB(P.capitalize(), callback_data='place_'+P), ])
         #XXX bug??
   # If personal location is available
   if personal:
      keyboard.append([IlKB(text="Ubicación Personalizada", 
                            callback_data='place_personal',
                            request_location=True)])
   keyboard.append( reset_options(main_callback,restart) )
   return InlineKeyboardMarkup(keyboard)

def localization(restart=False):
   keyboard = [[IlKB('Meteograma', callback_data=f'set_oper_meteogram')]]
   keyboard.append( reset_options(restart=restart) )
   return InlineKeyboardMarkup(keyboard)

def day(main_callback,restart=True):
   keyboard = [[IlKB('Hoy', callback_data='day_0'),
                IlKB('Mañana', callback_data='day_1')],
               [IlKB('Pasado', callback_data='day_2'),
                IlKB('Al otro', callback_data='day_3')]]
   keyboard.append( reset_options(main_callback,restart=restart) )
   return InlineKeyboardMarkup(keyboard)

def hour(main_callback,offer_vid=True,restart=True):
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
   keyboard.append( reset_options(main_callback, restart=restart) )
                  # [IlKB('Volver a empezar', callback_data='main'),
                  #  IlKB('Cancelar', callback_data='stop')]]
   return InlineKeyboardMarkup(keyboard)

def aemet(main_callback,restart=False):
   # Missing  aemet_lightning
   keyboard = [[IlKB('Viento', callback_data='aemet_wind'),
                IlKB('Racha Máx.', callback_data='aemet_gust')],
               [IlKB('Temperatura', callback_data='aemet_temperature'),
                IlKB('Presión', callback_data='aemet_press')],
               [IlKB('Lluvia (1h)', callback_data='aemet_rain'),
                IlKB('Nubosidad', callback_data='aemet_clouds')]                ]
   keyboard.append( reset_options(main_callback,restart=restart) )
   return InlineKeyboardMarkup(keyboard)

############################# Messages #########################################
def vector_msg():
   return 'Flujo de viento:'

def scalar_msg():
   return 'Propiedad:'

def cover_msg():
   return 'Cobertura:'

def day_msg(warn=False):
   txt = 'Elige día:'
   if warn:
      txt +=  '\n(puede que no todos los días estén disponibles)'
   return txt

def hour_msg(warn=False):
   txt = 'Elige hora:'
   if warn:
      txt += '\n(puede que no todas las horas estén disponibles)'
   return txt

def finalmsg():
   return 'Enviando:'

def places_msg():
   return 'Elige zona:'

def aemet_msg():
   txt = 'Esta opción te permite conseguir los *Modelos Numéricos* de Aemet.\n'
   txt += '(Modelo Harmonie Arome por ccaa)\n'
   txt += 'En ningún caso garantizo su integridad'
   txt += ', y recomiendo visitar la fuente:\n'
   txt += 'https://www.aemet.es/es/eltiempo/prediccion/modelosnumericos/harmonie_arome'
   return txt

def meteogram_msg():
   txt = 'Elige ubicación:'
   return txt
