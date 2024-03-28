#!/usr/bin/env python3
# train_models.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.neural_network import MLPRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor, StackingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_squared_log_error, explained_variance_score, median_absolute_error
from sklearn.preprocessing import OneHotEncoder
from joblib import dump
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Загрузка данных
file_path = 'basketball2.csv'
data = pd.read_csv(file_path)

# Кодирование категориальных признаков
categorical_features = ['awayTeam', 'homeTeam']
one_hot_encoder = OneHotEncoder(handle_unknown='ignore')
encoded_features = one_hot_encoder.fit_transform(data[categorical_features]).toarray()
feature_names = one_hot_encoder.get_feature_names_out(categorical_features)
encoded_df = pd.DataFrame(encoded_features, columns=feature_names)

X = pd.concat([encoded_df, data[['firstQuarterAwayScore', 'firstQuarterHomeScore', 'secondQuarterAwayScore', 'secondQuarterHomeScore', 'thirdQuarterAwayScore', 'thirdQuarterHomeScore']]], axis=1)

y_updated = {
    'total': data['totalScores'],
    'home': data['home'],
    'away': data['away'],
}

base_models = [
    ('XGBRegressor', XGBRegressor(objective='reg:squarederror')),
    ('CatBoostRegressor', CatBoostRegressor(verbose=0)),
    ('RandomForestRegressor', RandomForestRegressor()),
    ('Ridge', Ridge(alpha=1)),
    ('GradientBoostingRegressor', GradientBoostingRegressor()),
    ('MLPRegressor', MLPRegressor(max_iter=10000))
]

meta_model = LinearRegression()

for target, y_target in y_updated.items():
    print(f"Processing {target}...")
    for name, model in base_models:
        scores = cross_val_score(model, X, y_target, cv=5, scoring='neg_mean_squared_error')
        print(f"Cross-validated scores for {name} on {target}: {np.mean(scores):.2f}")

stacked_models = {}

for target, y_target in y_updated.items():
    print(f"Processing {target}...")
    X_train, X_test, y_train, y_test = train_test_split(X, y_target, test_size=0.2, random_state=42)

    stacked_regressor = StackingRegressor(estimators=base_models, final_estimator=meta_model, cv=5)
    stacked_regressor.fit(X_train, y_train)

    model_filename = f'model_{target}.joblib'
    dump(stacked_regressor, model_filename)
    print(f"Saved {target} model as {model_filename}")

    y_pred = stacked_regressor.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse_val = np.sqrt(mse)
    r2_val = r2_score(y_test, y_pred)
    explained_variance = explained_variance_score(y_test, y_pred)
    median_ae = median_absolute_error(y_test, y_pred)
    try:
        msle_val = mean_squared_log_error(y_test, y_pred)
    except ValueError:
        msle_val = 'не вычисляется из-за отрицательных предсказаний'

    print(f"MSE: {mse:.2f}, MAE: {mae:.2f}, RMSE: {rmse_val:.2f}, MSLE: {msle_val}, R2: {r2_val:.2f}, Explained Variance: {explained_variance:.2f}, Median AE: {median_ae:.2f}")

    stacked_models[target] = stacked_regressor

dump(one_hot_encoder, 'one_hot_encoder.joblib')
print("Saved OneHotEncoder as one_hot_encoder.joblib")
