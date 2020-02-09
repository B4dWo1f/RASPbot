#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
URL: http://www.aemet.es/es/eltiempo/prediccion/montana?w=XXdayXX&p=XXplaceXX

donde XXdayXX puede ser:
w=2 --> hoy
w=3 --> mañana
w=4 --> pasado
w=5 --> al otro
w=6 --> al siguiente

y XXplaceXX:
gre1 --> gredos
mad2 --> guadarrama
rio1 --> Ibérica Riojana (quizás toca la parte de Soria del RASP?)
arn2 --> Ibérica Aragonesa (creo q no llega a salir en el rasp)
"""

import datetime as dt
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import logging
LG = logging.getLogger(__name__)

names = {'gre1':'Gredos', 'mad2':'Guadarrama', 'rio1':'Rioja', 'arn2':'Aragon'}

def make_request(url):
   """ Make http request """
   req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
   html_doc = urlopen(req)
   html_doc = html_doc.read().decode(html_doc.headers.get_content_charset())
   return html_doc

def make_request1(url):
   """ Make http request """
   req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
   html_doc = urlopen(req)
   html_doc = html_doc.read()
   return html_doc

class AemetMontana(object):
   def __init__(self,place,val,txt):
      pattern  = r'Estado del cielo:([ ^\W\w\d_ ]*).'
      pattern += r'Precipitaciones:([ ^\W\w\d_ ]*).'
      pattern += r'Tormentas:([ ^\W\w\d_ ]*).'
      pattern += r'Temperaturas:([ ^\W\w\d_ ]*).'
      pattern += 'Viento:([ ^\W\w\d_ ]*)'
      match = re.search(pattern, txt)
      sky, precip, storm, temp, wind = match.groups()
      # Setup the class attributes
      self.place = place
      self.valid = val
      self.sky = sky
      self.precip = precip
      self.storm = storm
      self.temp = temp
      self.wind = wind
   def __str__(self):
      msg =  f'Report for {self.place}:\n'
      msg += f'{self.valid}\n'
      msg += f'  - Estado del cielo: {self.sky}\n'
      msg += f'  - Precipitaciones: {self.precip}\n'
      msg += f'  - Tormentas: {self.storm}\n'
      msg += f'  - Temperaturas: {self.temp}\n'
      msg += f'  - Vientos: {self.wind}'
      return msg

def parse_parte_aemet(url):
   html_doc = make_request(url)
   S = BeautifulSoup(html_doc, 'html.parser')
   place = S.find('h2', class_='titulo').text. split('.')[-1].strip()
   A = S.find('div', class_='texto_normal2 marginbottom35px')
   fcst = A.find('div',class_='texto_normal').text #.split('.')
   val = S.find_all('div', class_='notas_tabla')[-1].text.strip()
   return AemetMontana(place, val, fcst)

def get_temp(place, date):
   urls = {'arcones': 'http://www.aemet.es/xml/municipios_h/localidad_h_40020.xml',
       'bustarviejo': 'http://www.aemet.es/xml/municipios_h/localidad_h_28028.xml',
       'cebreros': 'http://www.aemet.es/xml/municipios_h/localidad_h_05057.xml',
       'abantos': 'http://www.aemet.es/xml/municipios_h/localidad_h_28054.xml',
       'piedrahita': 'http://www.aemet.es/xml/municipios_h/localidad_h_05186.xml',
       'pedro bernardo': 'http://www.aemet.es/xml/municipios_h/localidad_h_05182.xml',
       'lillo': 'http://www.aemet.es/xml/municipios_h/localidad_h_45084.xml',
       'fuentemilanos': 'http://www.aemet.es/xml/municipios_h/localidad_h_40001.xml',
       'candelario': 'http://www.aemet.es/xml/municipios_h/localidad_h_05021.xml',
       'pitolero': 'http://www.aemet.es/xml/municipios_h/localidad_h_10034.xml',
       'pegalajar': 'http://www.aemet.es/xml/municipios_h/localidad_h_23067.xml',
       'otivar': 'http://www.aemet.es/xml/municipios_h/localidad_h_18148.xml'}
   url = urls[place]

   doc = make_request1(url)
   S = BeautifulSoup(doc,'lxml')
   for dia in S.find_all('dia'):
      for T in dia.find_all('temperatura'):
         date_data = dia['fecha'] +' '+ T['periodo']+':00'
         date_data = dt.datetime.strptime(date_data, '%Y-%m-%d %H:%M')
         if date == date_data:
            return float(T.text)
   return None


def rain(T):
   """
   Returns the url for the image from Aemet's rain:
      Predicción > Modelos numéricos > HARMONIE-AROME CC. AA.
   """
   LG.info(f'Rain for {T}')
   url_base = 'https://www.aemet.es/imagenes_d/eltiempo/prediccion/modelos_num/'
   url_base += 'harmonie_arome_ccaa'
   now = dt.datetime.now()
   if dt.time(6,0) < now.time() < dt.time(14,0):
      print('6-12')
      ref = now.replace(hour=6,minute=0,second=0,microsecond=0)
      diff = T-ref
      diff = int(diff.total_seconds()/60/60) - 1
      url = f"{url_base}/{ref.strftime('%Y%m%d')}06+"
      url += f"{diff:03d}_ww_asx0d60{diff:02d}.png"
   else:
      ref = now.replace(hour=12,minute=0,second=0,microsecond=0)
      diff = T-ref
      diff = int(diff.total_seconds()/60/60) - 1
      url = f"{url_base}/{ref.strftime('%Y%m%d')}12+"
      url += f"{diff:03d}_ww_asx0d20{diff:02d}.png"
   print('****')
   print(url)
   print('****')
   LG.debug(url)
   return url
