# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 22:58:15 2019

@author: Kolomatskiy
"""

from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
import os
import time
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import googlemaps
import datetime

#this function allows to get typical time from realty to work or another destination
def get_time(coord, destination):
    apikey = 'AIzaSyCObRvNNnSal*******qBT5x7T8Gb6m0o' #you can get Google API key here: https://console.developers.google.com/?pli=1
    gmaps = googlemaps.Client(key=apikey)
    
    now = datetime.datetime.now()
    tuesday = now + datetime.timedelta( (1-now.weekday()) % 7 )
    
    departure = tuesday.replace(hour = 9, minute = 30, second = 0).timestamp()
    try:
        result = gmaps.directions(coord, destination, mode='transit', departure_time = departure)[0]
        return round(result['legs'][0]['duration']['value'] / 60)
    except Exception as e:
        print(e)

#this function retrieves link, address, price and description
def parseUrl(link):
    html = urlopen(link).read() 
    sp = BeautifulSoup(html, features="lxml")
    address = sp.find('div', 'adv_text').find('h1').text
    price = re.sub("[^0-9]", '', sp.find('div', 'price').text)
    description = sp.find('div', 'description').text.strip()
    try:
        coord = "".join(re.findall('[\d.,]', re.search('(center: \[).{16}(\])', str(sp.find_all('script')[4])).group(0)))
    except:
        coord = None
    workA = 'н/д'
    workK = 'н/д'
    if coord != None:    
        workA = get_time(coord, '59.9443,30.2950') #get travel time via PT to my work
        workK = get_time(coord, '59.9692,30.3157') #get travel time via PT to my friend's work
        
    return address, price, description, workA, workK


#this function sends an email with new entry to all recipients
def sendEmail(flat, path):
    recipients = ['andre-***@mail.ru', 'kirill****@mail.ru']
    
    addr_from = '***o**hkin@yandex.ru' #mail box created especially to send emails
    password  = '**sd***EDd' #password to this mail box
    
    COMMASPACE = ', '
    
    msg = MIMEMultipart()
    msg['From'] = formataddr((str(Header('Ёжкин Кот', 'utf-8')), addr_from))
    msg['To'] = COMMASPACE.join(recipients)
    msg['Subject'] = 'Новое объявление СТОП-Агент'
    
    body = ("Привет! На сайте СТОП Агент появилось новое объявление о сдаче 2х комнатной квартиры\n\nСсылка на объявление: %s" %flat['link']) + ("\nАдрес: %s" %flat['address']) + ("\nВремя до работы Кирилла на ОТ (вторник, 9:30): %s мин." %flat['workK']) + ("\nВремя до работы Андрея на ОТ (вторник, 9:30): %s мин." %flat['workA']) + ("\nЦена: %s руб." %flat['price']) + ("\n\nОписание: %s" %flat['description']) + ("\n\n\n\nАвтор скрипта: Андрей Коломацкий 🤘") 
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)
        server.login(addr_from, password)
        server.send_message(msg)
        server.quit()
        
        print("Message sent\n")
        writeFile(flat, path)
    except Exception as e:
        print(e)
    
def writeFile (flat, path):
    global data
    data = data.append(flat, ignore_index = True)
    data.to_csv(path, index = False)
     
#this function proccesses new entry
def newEntry(path, link):
    d = {'link' : link}
    d['address'], d['price'], d['description'], d['workA'], d['workK'] = parseUrl(link)
    if int(d['price']) <= 30000: #rent price should not be exceeded 30 000 run in our case
        sendEmail(d, path)

if __name__ == '__main__':
    path = os.path.join(os.getcwd(), "flat_data.csv")
    stations = ['м. Приморская', 'м. Василеостровская', 'м. Спортивная', 'м. Петроградская', 'м. Чкаловская', 'м. Горьковская',
                    'м. Маяковская', 'м. Пл.Восстания', 'м. Достоевская', 'м. Владимирская', 'м. Адмиралтейская',
                    'м. Технологич.ин.', 'м. Фрунзенская', 'м. Московск.ворота', 'м. Московская', 'м. Обводный канал', 'м. Электросила',
                    'м. Парк Победы', 'м. Невский пр.', 'м. Пр.Большевиков', 'м. Лиговский пр.', 'м. Звездная', 'м. Ул.Дыбенко']
    while True:
        if os.path.exists(path):
            data = pd.read_csv(path)
        else: 
            data = pd.DataFrame(columns = ['link', 'address', 'price', 'description', 'workA', 'workK'])
            
        html_doc = urlopen('http://stopagent.ru/arenda/long/2').read() 
        soup = BeautifulSoup(html_doc, features="lxml")
        for q in soup.find_all('div', 'search_results_text'):
            stroke = str(q.find('a'))
            metro = str(q.find('small').text.strip())
            if 'id' in stroke and metro in stations:
                link = "http://stopagent.ru" + str(re.findall(r'"(.*?)"', stroke)[0])
                if link not in str(data['link']):
                    newEntry(path, link)
            time.sleep(60)
        time.sleep(900)
        
