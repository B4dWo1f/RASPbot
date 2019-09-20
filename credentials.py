#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from base64 import b64decode as decode
from base64 import b64encode as encode
from functools import wraps
import os
here = os.path.dirname(os.path.realpath(__file__))

ADMINS_un = open(here+'/username.whitelist','r').read().strip().splitlines()
ADMINS_id = open(here+'/chatid.whitelist','r').read().strip().splitlines()
ADMINS_id = [int(x) for x in ADMINS_id]

def encode_credentials(key, chatid, fname='bot.token'):
   """ Encode the key and main chatid in a file """
   key    = encode(bytes(key,'utf-8')).decode('utf-8')
   chatid = encode(bytes(chatid,'utf-8')).decode('utf-8')
   with open(fname,'w') as f:
      f.write( key +'\n'+ chatid +'\n')
   f.close()

def get_credentials(api_file=here+'/telegram_bot.private'):
   """ decode the key and main chatid from a file """
   api_key = open(api_file,'r').read().strip().splitlines()
   bot_token = decode(api_key[0]).decode('utf-8')
   bot_chatID = decode(api_key[1]).decode('utf-8')
   return bot_token, bot_chatID

def restricted(func):
   """ Decorator to restrict the use of certain functions """
   @wraps(func)
   def wrapped(update, context, *args, **kwargs):
      user_id = update.effective_user.id
      user_nm = update.effective_user.username
      chatID = update.message.chat_id
      if user_id not in ADMINS_id or user_nm not in ADMINS_un:
         txt = "Unauthorized access denied for %s (%s)"%(user_nm,user_id)
         context.bot.send_message(chat_id=chatID, text=txt, parse_mode='Markdown')
         return
      return func(update, context, *args, **kwargs)
   return wrapped

if __name__ == '__main__':
   import sys
   try: key,chatID = sys.argv[1:]
   except IndexError:
      print('File not specified')
      exit()
   encode_credentials(key, chatID)
