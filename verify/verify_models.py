import os
import joblib
import xgboost as xgb
import numpy as np
import pandas as pd

# ===============================
# Resolve models directory safely
# ===============================
BASE_DIR = os.path.dirname(__file__)            # verify/
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")

# ===============================
# 🔍 VERIFY MODEL 1 (Fraud Classifier)
# ===============================
print("🔍 Verifying Model 1...")
model1 = joblib.load(os.path.join(MODELS_DIR, "model1.pkl"))
print("✅ Model 1 loaded")

model1_input = pd.DataFrame([{
    "time_since_complaint_min": 15,
    "complaint_hour": 14,
    "fraud_amount": 5000,
    "num_failed_txns_recent": 1,
    "account_fraud_count_30d": 1,
    "account_withdrawal_freq_30d": 8,
    "is_night_time": 0,
    "amount_bucket": "high",
    "fraud_type": "UPI",
    "bank_type": "private"
}])

print("Prediction:", model1.predict(model1_input))


# ===============================
# 🔍 VERIFY MODEL 2 (ATM Ranking Model)
# ===============================
print("\n🔍 Verifying Model 2...")
model2 = xgb.Booster()
model2.load_model(os.path.join(MODELS_DIR, "model2.json"))
print("✅ Model 2 loaded")

sample_rank = xgb.DMatrix(np.array([[0.5, 1.2, 3.4]]))
print("Prediction:", model2.predict(sample_rank))


# ===============================
# 🔍 VERIFY MODEL 3 (Withdrawal Time Predictor)
# ===============================
print("\n🔍 Verifying Model 3...")
model3 = joblib.load(os.path.join(MODELS_DIR, "model3.pkl"))
print("✅ Model 3 loaded")

model3_input = pd.DataFrame([{
    "complaint_hour": 14,
    "day_of_week": 3,
    "is_weekend": 0,
    "fraud_amount": 5000,
    "avg_time_to_withdrawal_past": 20,
    "num_prior_fraud_cases": 1
}])

print("Prediction:", model3.predict(model3_input))


# ===============================
# 🔍 VERIFY MODEL 4 (ATM Hotspot Model)
# ===============================
print("\n🔍 Verifying Model 4...")
model4 = xgb.Booster()
model4.load_model(os.path.join(MODELS_DIR, "model4.json"))
print("✅ Model 4 loaded")

hotspot_sample = xgb.DMatrix(np.array([
    [0.4, 5, 10, 300, 0.3, 0.1, 0.5]
]))

print("Prediction:", model4.predict(hotspot_sample))
