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

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re

names = {'gre1':'Gredos', 'mad2':'Guadarrama', 'rio1':'Rioja', 'arn2':'Aragon'}

def make_request(url):
   """ Make http request """
   req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
   html_doc = urlopen(req)
   html_doc = html_doc.read().decode(html_doc.headers.get_content_charset())
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

