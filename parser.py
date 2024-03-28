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

df = pd.DataFrame(list(collection.find()))

df.to_csv('basketball2.csv', index=False)