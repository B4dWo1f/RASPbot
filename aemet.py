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

def get_place_horas(place):
   url_base = 'https://www.aemet.es/es/eltiempo/prediccion/municipios/horas'
   # for k,v in codes.items():
   #    k = k.replace(' ','-')
   #    k = k.replace('abantos','escorial-el')
   #    k = k.replace('fuentemilanos','abades')
   #    k = k.replace('candelario','barco-de-avila-el')
   #    k = k.replace('pitolero','cabezabellosa')
   #    print(f'{url_base}/{k}-id{v}')
   urls = {'arcones':f'{url_base}/arcones-id40020',
           'bustarviejo':f'{url_base}/bustarviejo-id28028',
           'cebreros':f'{url_base}/cebreros-id05057',
           'abantos':f'{url_base}/escorial-el-id28054',
           'piedrahita':f'{url_base}/piedrahita-id05186',
           'pedro bernardo':f'{url_base}/pedro-bernardo-id05182',
           'lillo':f'{url_base}/lillo-id45084',
           'fuentemilanos':f'{url_base}/abades-id40001',
           'candelario':f'{url_base}/barco-de-avila-el-id05021',
           'pitolero':f'{url_base}/cabezabellosa-id10034',
           'pegalajar':f'{url_base}/pegalajar-id23067',
           'otivar':f'{url_base}/otivar-id18148'}
   return urls[place]

def get_temp(place, date):
   codes= {'arcones': '40020', 'bustarviejo': '28028', 'cebreros': '05057',
           'abantos': '28054', 'piedrahita': '05186', 'pedro bernardo': '05182',
           'lillo': '45084', 'fuentemilanos': '40001', 'candelario': '05021',
           'pitolero': '10034', 'pegalajar': '23067', 'otivar': '18148'}
   url = f'http://www.aemet.es/xml/municipios_h/localidad_h_{codes[place]}.xml'

   doc = make_request1(url)
   S = BeautifulSoup(doc,'lxml')
   for dia in S.find_all('dia'):
      for T in dia.find_all('temperatura'):
         date_data = dia['fecha'] +' '+ T['periodo']+':00'
         date_data = dt.datetime.strptime(date_data, '%Y-%m-%d %H:%M')
         if date == date_data:
            return float(T.text), get_place_horas(place)
   return None,None


def modelo_numerico(prop,T):
   """
   Returns the url for the image from Aemet's rain:
      Predicción > Modelos numéricos > HARMONIE-AROME CC. AA.
   """
   sufix = {'rain':'ww_asx', 'clouds':'ww_anx','temperature':'ww_atx',
            'press':'ww_a1x', 'wind':'wh_avx',
            'gust':'ww_arx', 'lightning':'ww_adx'}
   LG.info(f'{prop.capitalize()} for {T}')
   url_base = 'https://www.aemet.es/imagenes_d/eltiempo/prediccion/modelos_num/'
   url_base += 'harmonie_arome_ccaa'
   now = dt.datetime.now()
   if dt.time(6,0) < now.time() < dt.time(16,0):
      ref = now.replace(hour=6,minute=0,second=0,microsecond=0)
      diff = T-ref
      diff = int(diff.total_seconds()/60/60) - 1
      url = f"{url_base}/{ref.strftime('%Y%m%d')}06+"
      url += f"{diff:03d}_{sufix[prop]}0d60{diff:02d}.png"
   else:
      ref = now.replace(hour=12,minute=0,second=0,microsecond=0)
      diff = T-ref
      diff = int(diff.total_seconds()/60/60) - 1
      url = f"{url_base}/{ref.strftime('%Y%m%d')}12+"
      url += f"{diff:03d}_{sufix[prop]}0d20{diff:02d}.png"
   LG.debug(url)
   return url
