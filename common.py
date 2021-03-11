#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from configparser import ConfigParser, ExtendedInterpolation
from os.path import expanduser
import os
here = os.path.dirname(os.path.realpath(__file__))

fname = 'rasp_var.dict'
var_dict = open(fname,'r').read().strip()
keys,values = [],[]
for l in var_dict.splitlines():
   k,v = l.split(',')
   keys.append(k)
   values.append(v)
prop_names = dict(zip(keys,values))


command_callback = {'sfcwind':'sfcwind', 'blwind':'blwind',
                    'bltopwind':'bltopwind',
                    'techo':'hglider',
                    'cape':'cape',
                    'termicas':'wstar',
                    'convergencias':'wblmaxmin',
                    'base_nube':'zsfclcl',
                    'cubierta_nube':'zblcl',
                    'lluvia':'rain1'}


class RunParams(object):
   def __init__(self,t_del,t_renew,token_file,log,log_lv,DBname,fol_plots,
                                             fol_rplot, fol_data, do_broadcast):
      self.t_del = t_del
      self.t_renew = t_renew
      self.log = log
      self.log_lv = log_lv
      self.token_file = token_file
      self.DBname = DBname
      self.fol_plots = fol_plots
      self.fol_Rplots = fol_rplot   # Folder containing RASPlots
      self.fol_grids = f'{self.fol_Rplots}/grids'
      self.fol_data = fol_data
      self.do_broadcast = do_broadcast
   def __str__(self):
      txt =  f'Plots stored in: {self.fol_plots}\n'
      txt +=  f'Grids stored in: {self.fol_grids}\n'
      txt +=  f'Token file: {self.token_file}\n'
      txt += f'  Log file: {self.log} ({self.log_lv})\n'
      txt += f'   DB file: {self.DBname}\n'
      txt += f'T delete file: {self.t_del}\n'
      txt += f'T re-send file: {self.t_renew}'
      return txt


def load(fname='config.ini'):
   config = ConfigParser(inline_comment_prefixes='#')
   config._interpolation = ExtendedInterpolation()
   config.read(fname)

   t_del = eval(config['bot']['t_del'])
   t_renew = eval(config['bot']['t_renew'])
   token_file = config['bot']['token']
   if token_file[0] != '/': token_file = here + '/' + token_file
   fol_plots = expanduser(config['bot']['folder_plots'])
   fol_rplots = expanduser(config['bot']['folder_Rplots'])
   #fol_grids = expanduser(config['bot']['folder_grids'])
   fol_data = expanduser(config['bot']['folder_data'])
   do_broadcast = config['bot'].getboolean('do_broadcast')
   
   log = config['log']['log_file']
   levels = {'debug':10, 'info':20, 'warning':30, 'error':40, 'critical':50}
   log_lv = config['log']['log_level']
   log_lv = levels[log_lv.lower()]

   if log[0] != '/': log = here + '/' + log

   DBname = config['database']['db_name']

   RP = RunParams(t_del,t_renew, token_file,log,log_lv,DBname,
                  fol_plots,fol_rplots,fol_data,do_broadcast)
   return RP
