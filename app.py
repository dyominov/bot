from flask import Flask, request, jsonify
from joblib import load
import pandas as pd
import logging

app = Flask(__name__)

# Загрузка моделей и OneHotEncoder
model_total = load('model_total.joblib')
model_home = load('model_home.joblib')
model_away = load('model_away.joblib')
one_hot_encoder = load('one_hot_encoder.joblib')

file_path = 'basketball2.csv'
df = pd.read_csv(file_path)

threshold = 2  # Пороговое значение для сравнения экстремумов

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/predict', methods=['POST'])
def predict():
    games_data = request.json  # Список словарей с играми
    responses = []  # Список для хранения ответов на каждую игру

    for game in games_data:
        if 'awayTeam' not in game or 'homeTeam' not in game:
            logging.warning("В объекте игры отсутствуют ключи 'awayTeam' или 'homeTeam'")
            continue

        away_team = game['awayTeam']
        home_team = game['homeTeam']

        # Проверка наличия ключевых значений в игре
        if all(k in game for k in ('total', 'home', 'away')):
            current_total = game['total']
            current_home = game['home']
            current_away = game['away']
        else:
            logging.warning("Отсутствует один из ключей: 'total', 'home', 'away'")
            continue

        filtered_df = df[(df['homeTeam'] == home_team) & (df['awayTeam'] == away_team)]

        if filtered_df.empty:
            logging.warning(f"Данные для команд {home_team} и {away_team} не найдены")
            continue

        # Вычисление статистики по фильтрованному DataFrame
        stats = calculate_statistics(filtered_df)

        teams_for_prediction = pd.DataFrame({'awayTeam': [away_team], 'homeTeam': [home_team]})
        encoded_teams = one_hot_encoder.transform(teams_for_prediction).toarray()
        encoded_teams_df = pd.DataFrame(encoded_teams, columns=one_hot_encoder.get_feature_names_out())

        # Делаем предсказания
        predictions = {
            'total': model_total.predict(encoded_teams_df)[0],
            'home': model_home.predict(encoded_teams_df)[0],
            'away': model_away.predict(encoded_teams_df)[0]
        }

        # Проверяем условия для текущих и предсказанных значений
        messages = []
        messages += check_extremes_and_predictions(current_total, stats['total'], predictions['total'], 'total', threshold)
        messages += check_extremes_and_predictions(current_home, stats['home'], predictions['home'], 'home', threshold)
        messages += check_extremes_and_predictions(current_away, stats['away'], predictions['away'], 'away', threshold)

        # Формируем ответ для текущей игры
        responses.append({'homeTeam': home_team, 'awayTeam': away_team, 'messages': messages})

    # Возвращаем список ответов для всех игр
    return jsonify(responses)

def calculate_statistics(filtered_df):
    return {
        'total': {
            'min': filtered_df['totalScores'].min(),
            'max': filtered_df['totalScores'].max(),
            'mean': filtered_df['totalScores'].mean()
        },
        'home': {
            'min': filtered_df['home'].min(),
            'max': filtered_df['home'].max(),
            'mean': filtered_df['home'].mean()
        },
        'away': {
            'min': filtered_df['away'].min(),
            'max': filtered_df['away'].max(),
            'mean': filtered_df['away'].mean()
        }
    }

def check_extremes_and_predictions(current_value, stats, predicted_value, value_name, threshold):
    messages = []
    if abs(current_value - stats['mean']) > threshold:
        messages.append(f'Текущий {value_name} ({current_value}) значительно отличается от среднего ({stats["mean"]}).')
    if abs(current_value - stats['min']) <= threshold:
        messages.append(f'Текущий {value_name} ({current_value}) очень близок к минимальному значению ({stats["min"]}).')
    if abs(current_value - stats['max']) <= threshold:
        messages.append(f'Текущий {value_name} ({current_value}) очень близок к максимальному значению ({stats["max"]}).')
    if abs(current_value - predicted_value) > threshold:
        messages.append(f'Текущий {value_name} ({current_value}) сильно отличается от предсказанного значения ({predicted_value}).')
    return messages

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
