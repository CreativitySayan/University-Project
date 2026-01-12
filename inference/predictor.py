import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
import os

# ===============================
# Load all models ONCE
# ===============================

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")

# Model 1: Fraud occurrence classifier (sklearn)
fraud_classifier = joblib.load(os.path.join(MODELS_DIR, "model1.pkl"))

# Model 2: ATM ranking model (XGBoost Ranker)
atm_ranker = xgb.Booster()
atm_ranker.load_model(os.path.join(MODELS_DIR, "model2.json"))

# Model 3: Withdrawal time predictor (sklearn)
time_predictor = joblib.load(os.path.join(MODELS_DIR, "model3.pkl"))

# Model 4: ATM hotspot risk model (XGBoost Regressor)
hotspot_model = xgb.Booster()
hotspot_model.load_model(os.path.join(MODELS_DIR, "model4.json"))


# ===============================
# Main inference function
# ===============================
def predict_withdrawal_risk(
    complaint_features: dict,
    atm_feature_matrix: np.ndarray
):
    """
    complaint_features : dict
        Features related to the complaint / victim

    atm_feature_matrix : np.ndarray
        Shape (N, F) where N = number of candidate ATMs

    Returns:
        dict with actionable intelligence
    """

    # -------------------------------
    # 1️⃣ Model 1 – Will withdrawal happen?
    # -------------------------------
    complaint_df = pd.DataFrame([complaint_features])
    withdrawal_likely = int(fraud_classifier.predict(complaint_df)[0])

    if withdrawal_likely == 0:
        return {
            "withdrawal_likely": False,
            "action": "NO_ACTION_REQUIRED"
        }

    # -------------------------------
    # 2️⃣ Model 3 – When will it happen?
    # -------------------------------
    time_features = complaint_df[[
        "complaint_hour",
        "day_of_week",
        "is_weekend",
        "fraud_amount",
        "avg_time_to_withdrawal_past",
        "num_prior_fraud_cases"
    ]]

    estimated_time_min = float(time_predictor.predict(time_features)[0])

    # -------------------------------
    # 3️⃣ Model 2 – Rank ATMs
    # -------------------------------
    atm_dmatrix = xgb.DMatrix(atm_feature_matrix)
    ranking_scores = atm_ranker.predict(atm_dmatrix)

    # -------------------------------
    # 4️⃣ Model 4 – Hotspot risk
    # -------------------------------
    hotspot_scores = hotspot_model.predict(atm_dmatrix)

    # -------------------------------
    # Combine ATM risk scores
    # -------------------------------
    final_scores = ranking_scores * hotspot_scores

    ranked_atms = sorted(
        [
            {
                "atm_index": i,
                "risk_score": float(final_scores[i])
            }
            for i in range(len(final_scores))
        ],
        key=lambda x: x["risk_score"],
        reverse=True
    )

    # -------------------------------
    # Decide action
    # -------------------------------
    if estimated_time_min <= 20:
        action = "IMMEDIATE_ALERT"
    elif estimated_time_min <= 40:
        action = "MONITOR"
    else:
        action = "LOW_URGENCY"

    return {
        "withdrawal_likely": True,
        "estimated_time_minutes": round(estimated_time_min, 2),
        "top_atms": ranked_atms[:3],
        "action": action
    }
