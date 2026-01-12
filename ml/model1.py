import os
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier

# -------------------------
# Create models folder
# -------------------------
os.makedirs("../models", exist_ok=True)

# -------------------------
# Dummy training data (replace later with real data)
# -------------------------
data = {
    'time_since_complaint_min': [5, 15, 30, 60],
    'complaint_hour': [10, 14, 20, 23],
    'fraud_amount': [2000, 8000, 1500, 12000],
    'num_failed_txns_recent': [0, 1, 2, 3],
    'account_fraud_count_30d': [0, 1, 1, 2],
    'account_withdrawal_freq_30d': [5, 8, 6, 12],
    'is_night_time': [0, 0, 1, 1],
    'amount_bucket': ['low', 'high', 'low', 'high'],
    'fraud_type': ['UPI', 'Card', 'UPI', 'NetBanking'],
    'bank_type': ['private', 'public', 'private', 'private'],
    'label': [0, 1, 1, 1]
}

df = pd.DataFrame(data)
X = df.drop("label", axis=1)
y = df["label"]

# -------------------------
# Feature groups
# -------------------------
numeric_features = [
    'time_since_complaint_min',
    'complaint_hour',
    'fraud_amount',
    'num_failed_txns_recent',
    'account_fraud_count_30d',
    'account_withdrawal_freq_30d'
]

categorical_features = [
    'is_night_time',
    'amount_bucket',
    'fraud_type',
    'bank_type'
]

# -------------------------
# Pipeline
# -------------------------
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ]
)

fraud_classifier = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(
        n_estimators=100,
        class_weight='balanced',
        random_state=42
    ))
])

# -------------------------
# Train & Save
# -------------------------
fraud_classifier.fit(X, y)
joblib.dump(fraud_classifier, "../models/model1.pkl")

print("✅ model1.pkl created successfully")
