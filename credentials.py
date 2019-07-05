#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from base64 import b64decode as decode
from functools import wraps
import os
here = os.path.dirname(os.path.realpath(__file__))

LIST_OF_ADMINS_un = open('username.whitelist','r').read().strip().splitlines()
LIST_OF_ADMINS_id = open('chatid.whitelist','r').read().strip().splitlines()
LIST_OF_ADMINS_id = [int(x) for x in LIST_OF_ADMINS_id]

def get_credentials(api_file=here+'/telegram_bot.private'):
   api_key = open(api_file,'r').read().strip().splitlines()
   bot_token = decode(api_key[0]).decode('utf-8')
   bot_chatID = decode(api_key[1]).decode('utf-8')
   return bot_token, bot_chatID


def restricted(func):
   @wraps(func)
   def wrapped(bot, update, *args, **kwargs):
      user_id = update.effective_user.id
      user_nm = update.effective_user.username
      chatID = update.message.chat_id
      if user_id not in LIST_OF_ADMINS_id or user_nm not in LIST_OF_ADMINS_un:
         txt = "Unauthorized access denied for %s (%s)"%(user_nm,user_id)
         bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')
         return
      return func(bot, update, *args, **kwargs)
   return wrapped
