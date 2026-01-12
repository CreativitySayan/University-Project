from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from inference.predictor import predict_withdrawal_risk

app = FastAPI(title="Cybercrime Withdrawal Prediction API")

# -------------------------
# CORS (needed for browser)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Request schema
# -------------------------
class ComplaintInput(BaseModel):
    time_since_complaint_min: int
    complaint_hour: int
    fraud_amount: float
    num_failed_txns_recent: int
    account_fraud_count_30d: int
    account_withdrawal_freq_30d: int
    is_night_time: int
    amount_bucket: str
    fraud_type: str
    bank_type: str
    day_of_week: int
    is_weekend: int
    avg_time_to_withdrawal_past: int
    num_prior_fraud_cases: int


# -------------------------
# Health check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Prediction endpoint
# -------------------------
@app.post("/predict")
def predict(data: ComplaintInput):

    # Dummy ATM feature matrix (future: DB/PostGIS)
    atm_features = np.array([
        [0.5, 3, 0.6],
        [1.2, 5, 0.8],
        [0.8, 2, 0.7]
    ])

    result = predict_withdrawal_risk(
        complaint_features=data.dict(),
        atm_feature_matrix=atm_features
    )

    return result


# -------------------------
# Serve Frontend (VERY IMPORTANT)
# -------------------------
app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)
