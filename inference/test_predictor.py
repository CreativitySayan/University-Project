import numpy as np
from predictor import predict_withdrawal_risk

complaint_data = {
    "time_since_complaint_min": 15,
    "complaint_hour": 14,
    "fraud_amount": 5000,
    "num_failed_txns_recent": 1,
    "account_fraud_count_30d": 1,
    "account_withdrawal_freq_30d": 8,
    "is_night_time": 0,
    "amount_bucket": "high",
    "fraud_type": "UPI",
    "bank_type": "private",
    "day_of_week": 3,
    "is_weekend": 0,
    "avg_time_to_withdrawal_past": 20,
    "num_prior_fraud_cases": 1
}

atm_features = np.array([
    [0.5, 3, 0.6],
    [1.2, 5, 0.8],
    [0.8, 2, 0.7]
])

result = predict_withdrawal_risk(complaint_data, atm_features)
print(result)
