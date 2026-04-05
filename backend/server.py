from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Cookie, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import pandas as pd
import numpy as np
from io import StringIO, BytesIO
import json
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import xgboost as xgb
import pickle
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ MODELS ============

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "viewer"  # admin, analyst, viewer
    created_at: datetime

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime

class Complaint(BaseModel):
    complaint_id: str
    user_id: str
    complaint_time: datetime
    complaint_type: str
    location: str
    description: str
    status: str
    created_at: datetime

class Prediction(BaseModel):
    prediction_id: str
    complaint_id: str
    risk_score: float
    is_anomaly: bool
    model_version: str
    created_at: datetime

class Alert(BaseModel):
    alert_id: str
    complaint_id: str
    alert_type: str  # high_risk, anomaly
    severity: str  # low, medium, high, critical
    message: str
    is_read: bool = False
    created_at: datetime

class UploadResponse(BaseModel):
    message: str
    total_records: int
    complaints_created: int
    predictions_created: int
    alerts_created: int

class DashboardStats(BaseModel):
    total_complaints: int
    high_risk_count: int
    anomaly_count: int
    alerts_count: int
    risk_distribution: Dict[str, int]
    category_counts: Dict[str, int]
    recent_trends: List[Dict[str, Any]]

# ============ AUTHENTICATION HELPERS ============

async def get_current_user(
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Extract user from session token (cookie or Authorization header).
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    token = session_token
    
    # Fallback to Authorization header if no cookie
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        else:
            token = authorization
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session in database
    session_doc = await db.user_sessions.find_one(
        {"session_token": token},
        {"_id": 0}
    )
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**user_doc)

async def require_role(user: User, allowed_roles: List[str]):
    """Check if user has required role"""
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
        )

# ============ MACHINE LEARNING HELPERS ============

class MLModels:
    """Singleton class to store ML models"""
    risk_model = None
    anomaly_model = None
    label_encoders = {}
    model_version = "v1.0"

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess complaint data"""
    # Convert complaint_time to datetime
    if 'complaint_time' in df.columns:
        df['complaint_time'] = pd.to_datetime(df['complaint_time'])
        df['hour'] = df['complaint_time'].dt.hour
        df['day_of_week'] = df['complaint_time'].dt.dayofweek
        df['month'] = df['complaint_time'].dt.month
    
    # Handle missing values
    df = df.fillna({
        'complaint_type': 'Unknown',
        'location': 'Unknown',
        'description': '',
        'status': 'pending'
    })
    
    # Extract text length features
    df['description_length'] = df['description'].str.len()
    
    return df

def train_models(df: pd.DataFrame):
    """Train risk prediction and anomaly detection models"""
    logger.info(f"Training models with {len(df)} samples")
    
    # Prepare features
    feature_columns = ['hour', 'day_of_week', 'month', 'description_length']
    categorical_columns = ['complaint_type', 'location', 'status']
    
    # Encode categorical variables
    for col in categorical_columns:
        le = LabelEncoder()
        df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
        MLModels.label_encoders[col] = le
        feature_columns.append(f'{col}_encoded')
    
    X = df[feature_columns].values
    
    # Train anomaly detection model
    MLModels.anomaly_model = IsolationForest(
        contamination=0.1,
        random_state=42,
        n_estimators=100
    )
    MLModels.anomaly_model.fit(X)
    
    # Create synthetic risk labels based on patterns
    # Higher risk for: late hours, certain types, longer descriptions
    risk_factors = (
        (df['hour'] >= 22) | (df['hour'] <= 5)  # Late night
    ).astype(int) + (
        df['description_length'] > df['description_length'].median()
    ).astype(int)
    
    y = (risk_factors >= 1).astype(int)  # Binary risk
    
    # Train risk prediction model (Random Forest + XGBoost ensemble)
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X, y)
    
    xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42)
    xgb_model.fit(X, y)
    
    # Store ensemble
    MLModels.risk_model = {
        'rf': rf_model,
        'xgb': xgb_model
    }
    
    logger.info("Models trained successfully")

def predict_risk(features: Dict[str, Any]) -> Dict[str, Any]:
    """Predict risk score and detect anomalies"""
    if MLModels.risk_model is None or MLModels.anomaly_model is None:
        raise HTTPException(status_code=400, detail="Models not trained yet")
    
    # Prepare feature vector
    feature_list = [
        features.get('hour', 12),
        features.get('day_of_week', 0),
        features.get('month', 1),
        features.get('description_length', 0)
    ]
    
    # Encode categorical features
    for col in ['complaint_type', 'location', 'status']:
        if col in MLModels.label_encoders:
            le = MLModels.label_encoders[col]
            value = features.get(col, 'Unknown')
            try:
                encoded = le.transform([str(value)])[0]
            except:
                encoded = 0
            feature_list.append(encoded)
    
    X = np.array([feature_list])
    
    # Ensemble prediction (average of RF and XGBoost)
    rf_prob = MLModels.risk_model['rf'].predict_proba(X)[0][1]
    xgb_prob = MLModels.risk_model['xgb'].predict_proba(X)[0][1]
    risk_score = ((rf_prob + xgb_prob) / 2) * 100
    
    # Anomaly detection
    anomaly_pred = MLModels.anomaly_model.predict(X)[0]
    is_anomaly = anomaly_pred == -1
    
    return {
        'risk_score': float(risk_score),
        'is_anomaly': bool(is_anomaly)
    }

# ============ AUTH ENDPOINTS ============

@api_router.post("/auth/session")
async def create_session(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Exchange session_id for session_token.
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    try:
        # Call Emergent Auth API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session_id")
            
            auth_data = response.json()
        
        # Check if user exists
        user_doc = await db.users.find_one(
            {"email": auth_data["email"]},
            {"_id": 0}
        )
        
        if user_doc:
            user = User(**user_doc)
        else:
            # Create new user
            # First user gets admin role, others get viewer
            user_count = await db.users.count_documents({})
            role = "admin" if user_count == 0 else "viewer"
            
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            user = User(
                user_id=user_id,
                email=auth_data["email"],
                name=auth_data["name"],
                picture=auth_data.get("picture"),
                role=role,
                created_at=datetime.now(timezone.utc)
            )
            
            await db.users.insert_one(user.model_dump())
        
        # Create session
        session_token = auth_data["session_token"]
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        session = UserSession(
            user_id=user.user_id,
            session_token=session_token,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )
        
        await db.user_sessions.insert_one(session.model_dump())
        
        # Return user data with cookie
        response = JSONResponse(content=user.model_dump(mode='json'))
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=7*24*60*60,
            path="/"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_me(
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Get current user info"""
    try:
        user = await get_current_user(session_token, authorization)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get me error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/logout")
async def logout(
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Logout user"""
    token = session_token or (authorization.replace("Bearer ", "") if authorization else None)
    
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("session_token", path="/")
    return response

# ============ DATA UPLOAD ENDPOINTS ============

@api_router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Upload and process complaint dataset (CSV or JSON)"""
    user = await get_current_user(session_token, authorization)
    await require_role(user, ["admin", "analyst"])
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
        elif file.filename.endswith('.json'):
            df = pd.read_json(BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and JSON files supported")
        
        # Validate required columns
        required_cols = ['complaint_id', 'complaint_time', 'complaint_type', 'location', 'description', 'status']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        # Preprocess data
        df = preprocess_data(df)
        
        # Train models if not already trained or retrain with new data
        train_models(df)
        
        # Insert complaints and generate predictions
        complaints_created = 0
        predictions_created = 0
        alerts_created = 0
        
        for _, row in df.iterrows():
            # Create complaint
            complaint_id = str(row['complaint_id'])
            
            # Check if complaint already exists
            existing = await db.complaints.find_one({"complaint_id": complaint_id})
            if existing:
                continue
            
            complaint = Complaint(
                complaint_id=complaint_id,
                user_id=user.user_id,
                complaint_time=row['complaint_time'].to_pydatetime(),
                complaint_type=str(row['complaint_type']),
                location=str(row['location']),
                description=str(row['description']),
                status=str(row['status']),
                created_at=datetime.now(timezone.utc)
            )
            
            await db.complaints.insert_one(complaint.model_dump())
            complaints_created += 1
            
            # Generate prediction
            features = {
                'hour': row['hour'],
                'day_of_week': row['day_of_week'],
                'month': row['month'],
                'description_length': row['description_length'],
                'complaint_type': row['complaint_type'],
                'location': row['location'],
                'status': row['status']
            }
            
            pred_result = predict_risk(features)
            
            prediction = Prediction(
                prediction_id=f"pred_{uuid.uuid4().hex[:12]}",
                complaint_id=complaint_id,
                risk_score=pred_result['risk_score'],
                is_anomaly=pred_result['is_anomaly'],
                model_version=MLModels.model_version,
                created_at=datetime.now(timezone.utc)
            )
            
            await db.predictions.insert_one(prediction.model_dump())
            predictions_created += 1
            
            # Generate alerts if needed
            if pred_result['risk_score'] > 70 or pred_result['is_anomaly']:
                alert_type = "anomaly" if pred_result['is_anomaly'] else "high_risk"
                severity = "critical" if pred_result['risk_score'] > 85 else "high"
                
                message = f"High risk complaint detected: {row['complaint_type']} at {row['location']}"
                if pred_result['is_anomaly']:
                    message = f"Anomaly detected: Unusual pattern in {row['complaint_type']}"
                
                alert = Alert(
                    alert_id=f"alert_{uuid.uuid4().hex[:12]}",
                    complaint_id=complaint_id,
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                
                await db.alerts.insert_one(alert.model_dump())
                alerts_created += 1
        
        return UploadResponse(
            message="Dataset processed successfully",
            total_records=len(df),
            complaints_created=complaints_created,
            predictions_created=predictions_created,
            alerts_created=alerts_created
        )
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ DASHBOARD ENDPOINTS ============

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Get dashboard statistics"""
    user = await get_current_user(session_token, authorization)
    
    # Total complaints
    total_complaints = await db.complaints.count_documents({})
    
    # High risk count (risk_score > 70)
    high_risk_count = await db.predictions.count_documents({"risk_score": {"$gt": 70}})
    
    # Anomaly count
    anomaly_count = await db.predictions.count_documents({"is_anomaly": True})
    
    # Unread alerts count
    alerts_count = await db.alerts.count_documents({"is_read": False})
    
    # Risk distribution
    risk_low = await db.predictions.count_documents({"risk_score": {"$lt": 40}})
    risk_medium = await db.predictions.count_documents({"risk_score": {"$gte": 40, "$lt": 70}})
    risk_high = await db.predictions.count_documents({"risk_score": {"$gte": 70}})
    
    risk_distribution = {
        "Low": risk_low,
        "Medium": risk_medium,
        "High": risk_high
    }
    
    # Category counts
    pipeline = [
        {"$group": {"_id": "$complaint_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    category_results = await db.complaints.aggregate(pipeline).to_list(5)
    category_counts = {item["_id"]: item["count"] for item in category_results}
    
    # Recent trends (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    pipeline = [
        {"$match": {"created_at": {"$gte": seven_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    trend_results = await db.complaints.aggregate(pipeline).to_list(7)
    recent_trends = [{"date": item["_id"], "count": item["count"]} for item in trend_results]
    
    return DashboardStats(
        total_complaints=total_complaints,
        high_risk_count=high_risk_count,
        anomaly_count=anomaly_count,
        alerts_count=alerts_count,
        risk_distribution=risk_distribution,
        category_counts=category_counts,
        recent_trends=recent_trends
    )

@api_router.get("/complaints")
async def get_complaints(
    skip: int = 0,
    limit: int = 50,
    complaint_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Get complaints with optional filters"""
    user = await get_current_user(session_token, authorization)
    
    # Build query
    query = {}
    if complaint_type:
        query["complaint_type"] = complaint_type
    
    # Get complaints
    complaints = await db.complaints.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # If filtering by risk level, get predictions
    if risk_level:
        complaint_ids = [c["complaint_id"] for c in complaints]
        
        risk_query = {"complaint_id": {"$in": complaint_ids}}
        if risk_level == "Low":
            risk_query["risk_score"] = {"$lt": 40}
        elif risk_level == "Medium":
            risk_query["risk_score"] = {"$gte": 40, "$lt": 70}
        elif risk_level == "High":
            risk_query["risk_score"] = {"$gte": 70}
        
        predictions = await db.predictions.find(risk_query, {"_id": 0}).to_list(1000)
        pred_complaint_ids = {p["complaint_id"] for p in predictions}
        
        complaints = [c for c in complaints if c["complaint_id"] in pred_complaint_ids]
    
    # Attach predictions to complaints
    for complaint in complaints:
        pred = await db.predictions.find_one(
            {"complaint_id": complaint["complaint_id"]},
            {"_id": 0}
        )
        complaint["prediction"] = pred if pred else None
    
    return complaints

@api_router.get("/alerts")
async def get_alerts(
    skip: int = 0,
    limit: int = 50,
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Get alerts"""
    user = await get_current_user(session_token, authorization)
    
    alerts = await db.alerts.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return alerts

@api_router.patch("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Mark alert as read"""
    user = await get_current_user(session_token, authorization)
    
    result = await db.alerts.update_one(
        {"alert_id": alert_id},
        {"$set": {"is_read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert marked as read"}

# ============ ADMIN ENDPOINTS ============

@api_router.get("/admin/users")
async def get_users(
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Get all users (admin only)"""
    user = await get_current_user(session_token, authorization)
    await require_role(user, ["admin"])
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return users

@api_router.patch("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Update user role (admin only)"""
    user = await get_current_user(session_token, authorization)
    await require_role(user, ["admin"])
    
    if role not in ["admin", "analyst", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"role": role}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User role updated to {role}"}

@api_router.get("/admin/logs")
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Get system logs (admin only)"""
    user = await get_current_user(session_token, authorization)
    await require_role(user, ["admin"])
    
    # Return recent activities (complaints, predictions, alerts)
    complaints = await db.complaints.find({}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    predictions = await db.predictions.find({}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    alerts = await db.alerts.find({}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    
    logs = []
    
    for c in complaints:
        logs.append({
            "type": "complaint",
            "action": "created",
            "data": c,
            "timestamp": c["created_at"]
        })
    
    for p in predictions:
        logs.append({
            "type": "prediction",
            "action": "generated",
            "data": p,
            "timestamp": p["created_at"]
        })
    
    for a in alerts:
        logs.append({
            "type": "alert",
            "action": "triggered",
            "data": a,
            "timestamp": a["created_at"]
        })
    
    # Sort by timestamp
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return logs[skip:skip+limit]

# ============ GENERATE MOCK DATA ============

@api_router.post("/generate-mock-data")
async def generate_mock_data(
    count: int = 100,
    session_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    """Generate mock complaint data for testing"""
    user = await get_current_user(session_token, authorization)
    await require_role(user, ["admin", "analyst"])
    
    complaint_types = ["Noise", "Theft", "Vandalism", "Traffic", "Assault", "Fraud", "Burglary", "Harassment"]
    locations = ["Downtown", "Suburbs", "Industrial Area", "Residential Zone", "Shopping District", "Park", "Highway"]
    statuses = ["pending", "investigating", "resolved", "closed"]
    
    complaints_data = []
    
    for i in range(count):
        # Random timestamp in last 30 days
        days_ago = np.random.randint(0, 30)
        hours = np.random.randint(0, 24)
        complaint_time = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours)
        
        complaint_type = np.random.choice(complaint_types)
        location = np.random.choice(locations)
        status = np.random.choice(statuses)
        
        descriptions = [
            f"Reported {complaint_type.lower()} incident at {location}. Requires immediate attention.",
            f"Multiple complaints about {complaint_type.lower()} in {location} area.",
            f"Witness reported {complaint_type.lower()} near {location}. Investigation ongoing.",
            f"Ongoing {complaint_type.lower()} issue in {location}. Community concerned."
        ]
        
        complaints_data.append({
            "complaint_id": f"COMP{str(uuid.uuid4().hex[:8]).upper()}",
            "complaint_time": complaint_time.isoformat(),
            "complaint_type": complaint_type,
            "location": location,
            "description": np.random.choice(descriptions),
            "status": status
        })
    
    # Create DataFrame and save as JSON
    df = pd.DataFrame(complaints_data)
    json_data = df.to_json(orient='records')
    
    # Process the data through upload endpoint logic
    df = preprocess_data(df)
    train_models(df)
    
    complaints_created = 0
    predictions_created = 0
    alerts_created = 0
    
    for _, row in df.iterrows():
        complaint_id = str(row['complaint_id'])
        
        # Check if exists
        existing = await db.complaints.find_one({"complaint_id": complaint_id})
        if existing:
            continue
        
        complaint = Complaint(
            complaint_id=complaint_id,
            user_id=user.user_id,
            complaint_time=row['complaint_time'].to_pydatetime() if hasattr(row['complaint_time'], 'to_pydatetime') else pd.to_datetime(row['complaint_time']).to_pydatetime(),
            complaint_type=str(row['complaint_type']),
            location=str(row['location']),
            description=str(row['description']),
            status=str(row['status']),
            created_at=datetime.now(timezone.utc)
        )
        
        await db.complaints.insert_one(complaint.model_dump())
        complaints_created += 1
        
        features = {
            'hour': row['hour'],
            'day_of_week': row['day_of_week'],
            'month': row['month'],
            'description_length': row['description_length'],
            'complaint_type': row['complaint_type'],
            'location': row['location'],
            'status': row['status']
        }
        
        pred_result = predict_risk(features)
        
        prediction = Prediction(
            prediction_id=f"pred_{uuid.uuid4().hex[:12]}",
            complaint_id=complaint_id,
            risk_score=pred_result['risk_score'],
            is_anomaly=pred_result['is_anomaly'],
            model_version=MLModels.model_version,
            created_at=datetime.now(timezone.utc)
        )
        
        await db.predictions.insert_one(prediction.model_dump())
        predictions_created += 1
        
        if pred_result['risk_score'] > 70 or pred_result['is_anomaly']:
            alert_type = "anomaly" if pred_result['is_anomaly'] else "high_risk"
            severity = "critical" if pred_result['risk_score'] > 85 else "high"
            
            message = f"High risk complaint: {row['complaint_type']} at {row['location']}"
            if pred_result['is_anomaly']:
                message = f"Anomaly detected: {row['complaint_type']}"
            
            alert = Alert(
                alert_id=f"alert_{uuid.uuid4().hex[:12]}",
                complaint_id=complaint_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                is_read=False,
                created_at=datetime.now(timezone.utc)
            )
            
            await db.alerts.insert_one(alert.model_dump())
            alerts_created += 1
    
    return {
        "message": "Mock data generated successfully",
        "total_records": count,
        "complaints_created": complaints_created,
        "predictions_created": predictions_created,
        "alerts_created": alerts_created
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
