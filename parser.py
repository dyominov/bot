#!/usr/bin/env python3


import requests
import pymongo
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import pandas as pd

# Подключение к MongoDB
uri = "mongodb+srv://dyominov:1212dema@cluster0.v37qbx3.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client['basket']  # Замените на имя вашей базы данных
collection = db['basket2']  # Замените на имя вашей коллекции


def generate_url_with_unix_timestamp():
    # Получение текущего времени в секундах
    current_datetime = datetime.now(timezone.utc)
    current_seconds = int(current_datetime.timestamp())

    # Вычитание 3 часов из текущего времени для получения date_from_unix
    three_hours_ago = current_datetime - timedelta(hours=24)
    date_from_unix = int(three_hours_ago.timestamp())

    # Формирование URL с Unix timestamp в секундах
    url = (f'https://betwinner-843475.top/service-api/result/web/api/v1/games?champId=2626462'
           f'&dateFrom={date_from_unix}&dateTo={current_seconds}&lng=ru&ref=152&gr=495&country=2')
    print(url)
    return url

def transform_data(data):
    transformed_data = []
    for match in data['items']:
        quarters = match['score'].split(' ')[1].split(',')
        if len(quarters) > 4:
            continue
        quarter_scores = {'firstQuarter': {}, 'secondQuarter': {}, 'thirdQuarter': {}, 'fourthQuarter': {}}
        home_total = 0
        away_total = 0

        for i, quarter in enumerate(quarters):
            quarter = quarter.replace('(', '').replace(')', '')
            home_score, away_score = map(int, quarter.split(':'))
            quarter_name = list(quarter_scores.keys())[i]
            quarter_scores[quarter_name]['home'] = home_score
            quarter_scores[quarter_name]['away'] = away_score
            home_total += home_score
            away_total += away_score

        new_match = {
            '_id': match['id'],
            'awayTeam': match['opp2'],
            'homeTeam': match['opp1'],
            'competition': match['champName'],
            'date': match['dateStart'],
            'totalScores': home_total + away_total,
            'home': home_total,
            'away': away_total,
            'firstQuarterAwayScore': quarter_scores['firstQuarter']['away'],
            'firstQuarterHomeScore': quarter_scores['firstQuarter']['home'],
            'secondQuarterAwayScore': quarter_scores['secondQuarter']['away'],
            'secondQuarterHomeScore': quarter_scores['secondQuarter']['home'],
            'thirdQuarterAwayScore': quarter_scores['thirdQuarter']['away'],
            'thirdQuarterHomeScore': quarter_scores['thirdQuarter']['home'],
            'fourthQuarterAwayScore': quarter_scores['fourthQuarter']['away'],
            'fourthQuarterHomeScore': quarter_scores['fourthQuarter']['home']
        }
        transformed_data.append(new_match)
    return transformed_data

# Генерация URL
url = generate_url_with_unix_timestamp()

# Отправка запроса и получение ответа
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    transformed_data = transform_data(data)
    # Сохранение преобразованных данных в MongoDB
    collection.insert_many(transformed_data)
    print("Данные успешно сохранены в MongoDB")
else:
    print(f"Ошибка при получении данных: статус {response.status_code}")

df = pd.DataFrame(list(collection.find()))

df.to_csv('basketball2.csv', index=False)