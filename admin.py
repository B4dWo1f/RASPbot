#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlite3
from  sqlite3 import OperationalError
import logging
LG = logging.getLogger(__name__)

## Common tools ################################################################
class EntryNotFound(Exception):
   pass


## Gobal DataBase ##############################################################
def create_db(file_db='my_database.db'):
   """
   Create a database with two tables to store users and files
   Table users:
     chatid  username  first_name  last_name  is_admin
     [int]   [str]     [str]       [str]      [int]
   Table files:
     year   month  day    hour   minute  fname  file_id
     [int]  [int]  [int]  [int]  [int]   [str]  [str]
   """
   conn,c = connect(file_db=file_db)

   ## Users table
   field_types = ['chatid integer','username text','first_name text',
                  'last_name text','is_admin integer']
   field_types = ','.join(field_types)
   table = 'users'
   with conn:
      query = f"CREATE TABLE {table} ({field_types})"
      try: c.execute(query)
      except OperationalError:
         LG.warning(f'table {table} already exists')

   ## Files table
   field_types=['year integer', 'month integer', 'day integer', 'hour integer',
                'minute integer', 'fname text', 'file_id text']
   field_types = ','.join(field_types)
   table = 'files'
   with conn:
      query = f"CREATE TABLE {table} ({field_types})"
      try: c.execute(query)
      except OperationalError:
         LG.warning(f'table {table} already exists')
   return conn, c


def connect(file_db='my_database.db'):
   conn = sqlite3.connect(file_db)
   c = conn.cursor()
   return conn,c


def show_all(conn,table=None):
   c = conn.cursor()
   if table == None:
      c.execute("SELECT name FROM sqlite_master WHERE type='table';")
      tables = [t[0] for t in c.fetchall()]
      for table in tables:
         print(f'Table: {table}')
         show_all(conn,table=table)
         print('')
   else:
      c.execute(f'SELECT * FROM {table}')
      names = list(map(lambda x: x[0], c.description))
      print(*names)
      rows = c.fetchall()
      for row in rows:
         print(*row)
   c.close()


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
   c = conn.cursor()
   with conn:
      c.execute(f"DELETE from {table} WHERE {field}=:value",{'value': value})
   c.close()


## FILES #######################################################################
def insert_file(conn,year, month, day, hour, minute, fname, file_id):
   c = conn.cursor()
   with conn:
      try:
         ff = get_file(conn,'fname',fname)
         LG.warning('Entry already exists')
      except EntryNotFound:
         c.execute(f"INSERT INTO files VALUES (:year, :month, :day, :hour,"+
                   f":minute, :fname, :file_id)",
                   {'year':year, 'month':month, 'day':day, 'hour':hour,
                    'minute':minute, 'fname':fname, 'file_id':file_id})
   c.close()


def get_file(conn,field,value):
   ret = get_entry(conn,'files',field,value)
   if len(ret) > 0: return ret
   else: raise EntryNotFound

def remove_file(conn,field,value):
   ret = remove_entry(conn,'files',field,value)


## USERS #######################################################################
def insert_user(conn,chatid,uname,fname,lname,isadmin):
   c = conn.cursor()
   with conn:
      try:
         ff = get_user(conn,'username',uname)
         LG.warning('User already exists')
      except EntryNotFound:
         c.execute(f"INSERT INTO users VALUES (:pl0, :pl1, :pl2, :pl3, :pl4)",
                   {'pl0': chatid, 'pl1': uname, 'pl2': fname,
                    'pl3': lname, 'pl4':isadmin})
   c.close()


def get_user(conn,field,value):
   ret = get_entry(conn,'users',field,value)
   if len(ret) > 0: return ret
   else: raise EntryNotFound

def remove_user(conn,field,value):
   return remove_entry(conn,'users',field,value)



if __name__ == '__main__':
   import sys
   try: sqlite_file = sys.argv[1]
   except IndexError:
      print('No file specified')
      exit()

   #create_db(file_db=sqlite_file)
   conn,c = connect(sqlite_file)

   show_all(conn)
