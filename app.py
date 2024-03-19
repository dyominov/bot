from flask import Flask, render_template, request, jsonify
from joblib import load
import pandas as pd
import logging

app = Flask(__name__)

# Загружаем модели и OneHotEncoder
model_total = load('model_total.joblib')
model_home = load('model_home.joblib')
model_away = load('model_away.joblib')
one_hot_encoder = load('one_hot_encoder.joblib')

file_path = 'basketball2.csv'
df = pd.read_csv(file_path)

threshold = 2  # Пороговое значение для сравнения экстремумов
diff_threshold = 10  # Пороговое значение для сравнения с предсказаниями

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@app.route('/predict', methods=['POST'])
def predict():
    games_data = request.json  # Список словарей с играми
    responses = []  # Список для хранения ответов на каждую игру

    for game in games_data:
        away_team = game['awayTeam']
        home_team = game['homeTeam']
        if 'total' in game:
            current_total = game['total']
        else:
            logging.warning("'total' отсутствует в одном из объектов")
            continue
        if 'home' in game:
            current_home = game['home']
        else:
            # Если ключ 'total' отсутствует, можно задать значение по умолчанию или обработать иначе
            logging.warning("'total' отсутствует в одном из объектов")
            continue
        if 'away' in game:
            current_away = game['away']
        # Далее ваш код, который обрабатывает current_total
        else:
            # Если ключ 'total' отсутствует, можно задать значение по умолчанию или обработать иначе
            logging.warning("'total' отсутствует в одном из объектов")
            continue

    filtered_df = df[(df['homeTeam'] == home_team) & (df['awayTeam'] == away_team)]

    # Вычисляем статистику по фильтрованному DataFrame
    min_total_score, max_total_score = filtered_df['totalScores'].min(), filtered_df['totalScores'].max()
    mean_total_score = filtered_df['totalScores'].mean()
    min_home_score, max_home_score = filtered_df['home'].min(), filtered_df['home'].max()
    mean_home_score = filtered_df['home'].mean()
    min_away_score, max_away_score = filtered_df['away'].min(), filtered_df['away'].max()
    mean_away_score = filtered_df['away'].mean()

    teams_for_prediction = pd.DataFrame({'awayTeam': [away_team], 'homeTeam': [home_team]})
    encoded_teams = one_hot_encoder.transform(teams_for_prediction).toarray()
    encoded_teams_df = pd.DataFrame(encoded_teams, columns=one_hot_encoder.get_feature_names_out())

    # Делаем предсказания
    predicted_total = model_total.predict(encoded_teams_df)[0]
    predicted_home = model_home.predict(encoded_teams_df)[0]
    predicted_away = model_away.predict(encoded_teams_df)[0]

    # Проверяем условия для текущих и предсказанных значений
    messages = []
    check_extremes_and_predictions(messages, current_total, min_total_score, max_total_score, mean_total_score,
                                   predicted_total, 'тотал')
    check_extremes_and_predictions(messages, current_home, min_home_score, max_home_score, mean_home_score,
                                   predicted_home, 'домашний счет')
    check_extremes_and_predictions(messages, current_away, min_away_score, max_away_score, mean_away_score,
                                   predicted_away, 'выездной счет')

    # Формируем ответ для текущей игры
    responses.append({'homeTeam': home_team, 'awayTeam': away_team, 'messages': messages})

    # Возвращаем список ответов для всех игр
    return jsonify(responses)


def check_extremes_and_predictions(messages, current_value, min_value, max_value, mean_value, predicted_value,
                                   value_name):
    """Функция для проверки текущих и предсказанных значений."""
    if abs(current_value - mean_value) > diff_threshold or \
            abs(current_value - min_value) <= threshold or \
            abs(current_value - max_value) <= threshold or \
            abs(current_value - predicted_value) > diff_threshold:
        messages.append(
            f'Текущий {value_name} ({current_value}) выходит за рамки нормы или сильно отличается от предсказанного ({predicted_value}).')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
