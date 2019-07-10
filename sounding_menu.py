#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import datetime as dt
from telegram import InlineKeyboardButton as IlKB
from telegram import InlineKeyboardMarkup
from urllib.request import urlretrieve
import tool
import os
import aemet


def choose_place(bot, update, user_data):
   user_data = {}
   places = open('soundings.csv','r').read().strip().splitlines()
   places = dict([l.split(',') for l in places])
   places_keys = list(places.keys())
   keyboard = []
   for i in range(0,len(places_keys),2):
      try:
         P = places_keys[i]
         P1 = places_keys[i+1]
         keyboard.append([IlKB(P.capitalize(), callback_data=P),
                            IlKB(P1.capitalize(), callback_data=P1)])
      except IndexError:
         P = places_keys[i]
         keyboard.append([IlKB(P.capitalize(), callback_data=P), ])
   reply_markup = InlineKeyboardMarkup(keyboard)
   update.message.reply_text("Choose a place:", reply_markup=reply_markup)
   return 'SOU_PLACE'

def choose_date(bot, update, user_data):
   query = update.callback_query
   selection = query.data
   # save selection into user data
   user_data['sou_place'] = selection
   bot.edit_message_text(chat_id=query.message.chat_id,
                         message_id=query.message.message_id,
                         text=u"Selected: %s"%(query.data))
   now = dt.datetime.now()
   day = dt.timedelta(days=1)
   fmt = '%d/%m/%Y'
   keyboard = [[IlKB("Hoy", callback_data=now.strftime(fmt)),
                IlKB("Mañana", callback_data=(now+day).strftime(fmt))],
               [IlKB("Pasado", callback_data=(now+2*day).strftime(fmt)),
                IlKB("Al otro", callback_data=(now+3*day).strftime(fmt))] ]
   reply_markup = InlineKeyboardMarkup(keyboard)
   #update.message.reply_text("Choose date:", reply_markup=reply_markup)
   bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                 message_id=query.message.message_id,
                                 reply_markup=reply_markup)
   return 'SOU_TIME'

def choose_time(bot, update, user_data):
   query = update.callback_query
   selection = query.data
   # save selection into user data
   user_data['sou_date'] = selection
   bot.edit_message_text(chat_id=query.message.chat_id,
                         message_id=query.message.message_id,
                         text=u"Selected: %s"%(query.data))
   keyboard=[[IlKB("9:00",  callback_data='9:00') ,
              IlKB("10:00", callback_data='10:00'),
              IlKB("11:00", callback_data='11:00'),
              IlKB("12:00", callback_data='12:00')],
             [IlKB("13:00", callback_data='13:00') ,
              IlKB("14:00", callback_data='14:00'),
              IlKB("15:00", callback_data='15:00'),
              IlKB("16:00", callback_data='16:00')],
             [IlKB("17:00", callback_data='17:00') ,
              IlKB("18:00", callback_data='18:00'),
              IlKB("19:00", callback_data='19:00'),
              IlKB("20:00", callback_data='20:00')]]
   reply_markup = InlineKeyboardMarkup(keyboard)
   bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                 message_id=query.message.message_id,
                                 reply_markup=reply_markup)
   return 'SOU_SEND'

def send(bot, update, user_data, job_queue):
   # here I get my old selection
   #LG.info('received request: %s'%(update.message.text))
   places = {'arcones': 1, 'bustarviejo': 2, 'cebreros': 3, 'abantos': 4,
             'piedrahita': 5, 'pedro bernardo': 6, 'lillo': 7,
             'fuentemilanos': 8, 'candelario': 10, 'pitolero': 11,
             'pegalajar': 12, 'otivar': 13}
   query = update.callback_query
   chatID = query.message.chat_id
   selection = query.data
   place = user_data['sou_place']
   index = places[place]
   user_data['sou_time'] = selection
   bot.edit_message_text(chat_id=query.message.chat_id,
                         message_id=query.message.message_id,
                         text=u"Selected: %s"%(query.data))
   date = ' '.join([user_data['sou_date'],user_data['sou_time']])
   date = dt.datetime.strptime(date,'%d/%m/%Y %H:%M')
   fol,_ = tool.locate(date,'')
   H = date.strftime('%H%M')
   url_picture = 'http://raspuri.mooo.com/RASP/'
   url_picture += f'{fol}/FCST/sounding{index}.curr.{H}lst.w2.png'
   f_tmp = '/tmp/' + tool.rand_name() + '.png'
   urlretrieve(url_picture, f_tmp)
   T = aemet.get_temp(place,date)
   txt = "Sounding for _%s_ at %s"%(place.capitalize(), date.strftime('%d/%m/%Y-%H:%M'))
   if T != None:
      txt += '\nExpected temperature: *%s°C*'%(T)
   tool.send_picture(bot, chatID, job_queue, f_tmp, msg=txt, t=180,delete=True)
   os.system(f'rm {f_tmp}')
   #tool.send_picture(bot, chatID, job_queue, url_picture, msg=txt, t=30,delete=True)
   user_data = {}
   return
