#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from base64 import b64decode as decode
from base64 import b64encode as encode
import string
from random import choice
from functools import wraps
import os
here = os.path.dirname(os.path.realpath(__file__))

ADMINS = open(here+'/whitelist.private','r').read().strip().splitlines()
ADMINS_id = [int(x.split(',')[0]) for x in ADMINS]
ADMINS_un = [x.split(',')[1] for x in ADMINS]

class MyBot(object):
   def __init__(self, token, chatIDs):
      self.token = token
      self.chatIDs = chatIDs
      self.whitelist = ADMINS_id
      self.whitelist_id = self.whitelist
      self.whitelist_un = ADMINS_un
   def __str__(self):
      msg = f'Token: {self.token}\n'
      msg += 'Chat IDs:\n'
      for chid in self.chatIDs:
         msg += f'  --> {chid}\n'
      return msg

def encode_credentials(key, chatid):  #, fname='bot.token'):
   """ Encode the key and main chatid in a file """
   key    = encode(bytes(key,'utf-8')).decode('utf-8')
   chatid = encode(bytes(chatid,'utf-8')).decode('utf-8')
   return key, chatid

def get_credentials(api_file=here+'/telegram_bot.private'):
   """ decode the key and main chatid from a file """
   api_key = open(api_file,'r').read().strip().splitlines()
   bot_token = decode(api_key[0]).decode('utf-8')
   # bot_chatID = decode(api_key[1]).decode('utf-8')
   bot_chatIDs = [ decode(key).decode('utf-8') for key in api_key[1:] ]
   # return bot_token, bot_chatIDs
   return MyBot(bot_token, bot_chatIDs)

def rand_string(pwdSize=8):
   """ Generates a random string of letters and digits with pwdSize length """
   ## all possible letters and numbers
   chars = string.ascii_letters + string.digits
   return ''.join((choice(chars)) for x in range(pwdSize))


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
   try:
      key,chatID = sys.argv[1:]
      key,chatID = encode_credentials(key, chatID)
      print(key)
      print(chatID)
   except ValueError:
      token,chatID = get_credentials(sys.argv[1])
      print(token)
      print(chatID)
   except IndexError:
      print('File not specified')
      exit()
