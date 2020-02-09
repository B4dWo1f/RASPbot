#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlite3
from  sqlite3 import OperationalError
import logging
LG = logging.getLogger(__name__)

## Common tools ################################################################
class EntryNotFound(Exception):
   """
   Custom exception to report missing entry from the DB
   """
   pass


## Gobal DataBase ##############################################################
def create_db(file_db='my_database.db'):
   """
   Create a database with two tables to store users and files
      Table users:
        chatid  username  first_name  last_name  admin_level  usage
        [int]   [str]     [str]       [str]      [int]        [int]
      Table files:
        date_requested  date_prediction  vector  scalar  cover   file_id
        [text]          [text]           [text]  [text]  [text]  [text]
   admin_level is increasingly worse. admin_level=0 means god-like permissions
   admin_level=infinite means no access to the bot services.
   The actual levels will be set as the bot evolves
   """
   conn,c = connect(file_db=file_db)

   ## Users table
   field_types = ['chatid integer','username text','first_name text',
                  'last_name text','admin_level integer','usage integer']
   field_types = ','.join(field_types)
   table = 'users'
   with conn:
      query = f"CREATE TABLE {table} ({field_types})"
      try:
         LG.debug('Attempting to create DB')
         LG.debug(query)
         c.execute(query)
      except OperationalError:
         LG.warning(f'table {table} already exists')

   ## Files table
   field_types = ['date_requested text', 'date_prediction text', 'vector text',
                  'scalar text', 'cover text','file_id text']
   # field_types=['year integer', 'month integer', 'day integer', 'hour integer',
   #              'minute integer', 'fname text', 'file_id text']
   field_types = ','.join(field_types)
   table = 'files'
   with conn:
      query = f"CREATE TABLE {table} ({field_types})"
      try:
         LG.debug(f'Creating table {table}')
         LG.debug(query)
         c.execute(query)
      except OperationalError:
         LG.warning(f'table {table} already exists')
   return conn, c


def connect(file_db='my_database.db'):
   """
   Create a SQLite connection and cursor
   """
   LG.debug(f'Connecting to DB: {file_db}')
   conn = sqlite3.connect(file_db)
   c = conn.cursor()
   return conn,c


def show_all(conn,table=None):
   """ Return string with all the DB information """
   msg = ''
   c = conn.cursor()
   if table == None:
      c.execute("SELECT name FROM sqlite_master WHERE type='table';")
      tables = [t[0] for t in c.fetchall()]
      for table in tables:
         msg += f'Table: {table}\n'
         msg += show_all(conn,table=table)
         msg += '\n'
      msg += '\n'
   else:
      c.execute(f'SELECT * FROM {table}')
      names = list(map(lambda x: x[0], c.description))
      msg += ' '.join(names) + '\n'
      rows = c.fetchall()
      for row in rows:
         msg += ' '.join([str(x) for x in row]) + '\n'
      msg += '\n'
   c.close()
   return msg.strip()


def get_entry(conn,table,field,value):
   """
   field: name of the field to look the file by
   value: value to match field
   """
   c = conn.cursor()
   with conn:
      c.execute(f"SELECT * FROM {table} WHERE {field}=:val", {'val': value})
   ret = c.fetchall()
   c.close()
   return ret
   #if len(ret) > 0: return ret
   #else: raise EntryNotFound


def remove_entry(conn,table,field,value):
   """
   Remove an entry defined by field=value from the DB
   """
   c = conn.cursor()
   with conn:
      LG.debug(f"DELETE from {table} WHERE {field}={value}")
      c.execute(f"DELETE from {table} WHERE {field}=:value",{'value': value})
   c.close()


## FILES #######################################################################
def insert_file(conn, date_req, date_pred, vector, scalar, cover, file_id):
   """
   Insert sent file unless that entry already exists
   """
   vector = str(vector)
   scalar = str(scalar)
   cover = str(cover)
   c = conn.cursor()
   with conn:
      try:
         LG.debug('Inserting sent file')
         LG.debug(f'{date_pred}, {vector}, {scalar}, {cover}')
         ff = get_file(conn, date_pred, vector, scalar, cover)
         LG.warning('Entry already exists')
      except EntryNotFound:
         LG.debug(f'Inserting entry')
         msg =  f"INSERT INTO files VALUES ({date_req}, {date_pred},"
         msg += f" {vector}, {scalar}, {cover}, {file_id}"
         LG.debug(msg)
         query =  f"INSERT INTO files VALUES (:date_req, :date_pred, "
         query += f":vector, :scalar, :cover, :file_id)"
         c.execute(query,{'date_req':date_req, 'date_pred':date_pred,
                          'vector':vector, 'scalar':scalar, 'cover':cover,
                          'file_id':file_id})
   c.close()


def get_file(conn, date_pred, vector, scalar, cover,table='files'):
   """
   Retrieve sent file
   """
   c = conn.cursor()
   with conn:
      LG.debug('Retrieve file')
      LG.debug(f'{date_pred}, {vector}, {scalar}, {cover}')
      c.execute(f"SELECT * FROM {table} WHERE "+
                f"date_prediction=:pred AND "+
                f"vector=:vector AND "+
                f"scalar=:scalar AND "+
                f"cover=:cover",
                {'pred': date_pred,
                 'vector':vector,
                 'scalar':scalar,
                 'cover':cover})
   ret = c.fetchall()
   c.close()
   if len(ret) > 0: return ret
   else: raise EntryNotFound

def remove_file(conn,f_id,table='files'):
   # ret = remove_entry(conn,'files','file_id',f_id)
   c = conn.cursor()
   with conn:
      c.execute(f"DELETE from {table} WHERE file_id=:value",{'value': f_id})
   c.close()


## USERS #######################################################################
def user_usage(conn,chatid,usage):
   """
   Add "usage" to user's usage
   """
   LG.debug(f'Update usage for chat {chatid}')
   c = conn.cursor()
   with conn:
      current_usage = get_user(conn,'chatid',chatid)[0][-1]
      msg = f'Update usage from {current_usage} to'
      usage += current_usage
      msg += f' {usage}'
      LG.debug(msg)
      c.execute(f"UPDATE users SET usage=:usa WHERE chatid=:chatid",
                 {'usa':usage, 'chatid':chatid})


def insert_user(conn,chatid,uname,fname,lname,admin_level,usage=0):
   """
   Insert new user if it didn't exist previously
   """
   c = conn.cursor()
   with conn:
      try:
         ff = get_user(conn,'username',uname)
         LG.warning('User already exists')
      except EntryNotFound:
         msg = f'Inserting new user: {uname}, {fname}, {lname}, {admin_level}'
         LG.debug(msg)
         c.execute("INSERT INTO users VALUES "+
                   f"(:pl0, :pl1, :pl2, :pl3, :pl4, :pl5)",
                   {'pl0': chatid, 'pl1': uname, 'pl2': fname,
                    'pl3': lname, 'pl4':admin_level, 'pl5':usage})
   c.close()


def get_user(conn,field,value):
   """
   Retrieve user info from a DB
   field allows the definition of the field to look for (username, first_name or
   last_name)
   """
   ret = get_entry(conn,'users',field,value)
   if len(ret) > 0: return ret
   else: raise EntryNotFound


def remove_user(conn,field,value):
   """
   Remove user from DataBase
   """
   return remove_entry(conn,'users',field,value)



if __name__ == '__main__':
   import sys
   import datetime as dt
   try: sqlite_file = sys.argv[1]
   except IndexError:
      print('No file specified')
      exit()

   # create_db(file_db=sqlite_file)
   # conn,c = connect(sqlite_file)
   # req = dt.datetime.now()
   # val = dt.datetime.now()+dt.timedelta(days=3)
   # vec=None
   # scal='sfcwind'
   # cov=None
   # file_id = '2345ty6u7j6543re'
   # fmt = '%d/%m/%Y-%H:00'
   # insert_file(conn,req.strftime(fmt),val.strftime(fmt),vec,scal,cov,file_id)
   # print(show_all(conn))
   # print('\n\nRepeating\n')
   # insert_file(conn,req.strftime(fmt),val.strftime(fmt),vec,scal,cov,file_id)
   # print(show_all(conn))

   conn,c = connect(sqlite_file)
   print(show_all(conn))  #,"users"))
