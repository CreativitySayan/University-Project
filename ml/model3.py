import os
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor

os.makedirs("../models", exist_ok=True)

# Dummy data
data = {
    'complaint_hour': [10, 14, 20, 23],
    'day_of_week': [1, 3, 5, 6],
    'is_weekend': [0, 0, 0, 1],
    'fraud_amount': [2000, 8000, 1500, 12000],
    'avg_time_to_withdrawal_past': [20, 15, 30, 10],
    'num_prior_fraud_cases': [0, 1, 1, 2],
    'target_minutes': [25, 10, 20, 5]
}

df = pd.DataFrame(data)

X = df.drop("target_minutes", axis=1)
y = df["target_minutes"]

withdrawal_predictor = Pipeline(steps=[
    ('scaler', StandardScaler()),
    ('regressor', GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    ))
])

withdrawal_predictor.fit(X, y)
joblib.dump(withdrawal_predictor, "../models/model3.pkl")

print("✅ model3.pkl created successfully")
