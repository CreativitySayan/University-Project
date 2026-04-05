# CyberGuard Pro - Product Requirements Document

## Overview
CyberGuard Pro is an AI-powered Predictive Intelligence Platform for analyzing complaint/incident data, detecting patterns, predicting future risks, and generating alerts through an interactive mobile dashboard.

## Tech Stack
- **Frontend**: React Native (Expo), TypeScript
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Machine Learning**: Scikit-learn, XGBoost, Pandas, NumPy
- **Authentication**: Emergent Google Social Login
- **Charts**: React Native Gifted Charts
- **Navigation**: Expo Router (file-based routing)

## Features Implemented

### 1. Authentication & Authorization
- ✅ Emergent Google Social Login
- ✅ Role-based access control (Admin, Analyst, Viewer)
- ✅ Session management with JWT tokens
- ✅ Automatic role assignment (first user = admin, others = viewer)

### 2. Dashboard Module
- ✅ Real-time statistics display
  - Total complaints
  - High-risk count
  - Anomaly count
  - Active alerts
- ✅ Risk distribution visualization
- ✅ Top complaint categories
- ✅ Pull-to-refresh functionality
- ✅ Mock data generation for testing

### 3. Data Upload Module
- ✅ CSV/JSON file upload support
- ✅ Data validation and cleaning
- ✅ Automatic preprocessing
- ✅ Upload results summary
- ✅ Role restrictions (Admin/Analyst only)

### 4. Machine Learning Module
- ✅ **Risk Prediction Model**
  - Random Forest Classifier
  - XGBoost Classifier
  - Ensemble approach (averaging predictions)
  - Risk score (0-100)
- ✅ **Anomaly Detection**
  - Isolation Forest algorithm
  - Binary anomaly classification
- ✅ Feature Engineering
  - Time-based features (hour, day_of_week, month)
  - Text length features
  - Categorical encoding
- ✅ Model training on data upload
- ✅ Real-time predictions

### 5. Analytics Module
- ✅ Complaint list with predictions
- ✅ Risk score visualization
- ✅ Anomaly indicators
- ✅ Filtering by risk level
- ✅ Pull-to-refresh
- ✅ Detailed complaint cards

### 6. Alert System
- ✅ Automatic alert generation
  - High-risk complaints (score > 70)
  - Detected anomalies
- ✅ Severity levels (low, medium, high, critical)
- ✅ Alert types (high_risk, anomaly)
- ✅ Unread alert tracking
- ✅ Mark as read functionality
- ✅ Visual indicators

### 7. Admin Panel
- ✅ User management
  - View all users
  - Update user roles
- ✅ System logs
  - Complaint creation logs
  - Prediction generation logs
  - Alert trigger logs
- ✅ Activity tracking
- ✅ Admin-only access control

### 8. API Endpoints

#### Authentication
- `POST /api/auth/session` - Exchange session_id for token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user

#### Data Management
- `POST /api/upload` - Upload CSV/JSON dataset
- `POST /api/generate-mock-data` - Generate test data
- `GET /api/complaints` - Get complaints with filters
- `GET /api/dashboard/stats` - Get dashboard statistics

#### Alerts
- `GET /api/alerts` - Get all alerts
- `PATCH /api/alerts/{id}/read` - Mark alert as read

#### Admin
- `GET /api/admin/users` - Get all users
- `PATCH /api/admin/users/{id}/role` - Update user role
- `GET /api/admin/logs` - Get system logs

## Database Schema

### Collections

#### users
```javascript
{
  user_id: String,      // Custom UUID
  email: String,
  name: String,
  picture: String,
  role: String,         // admin | analyst | viewer
  created_at: DateTime
}
```

#### user_sessions
```javascript
{
  user_id: String,
  session_token: String,
  expires_at: DateTime,
  created_at: DateTime
}
```

#### complaints
```javascript
{
  complaint_id: String,
  user_id: String,
  complaint_time: DateTime,
  complaint_type: String,
  location: String,
  description: String,
  status: String,
  created_at: DateTime
}
```

#### predictions
```javascript
{
  prediction_id: String,
  complaint_id: String,
  risk_score: Float,    // 0-100
  is_anomaly: Boolean,
  model_version: String,
  created_at: DateTime
}
```

#### alerts
```javascript
{
  alert_id: String,
  complaint_id: String,
  alert_type: String,   // high_risk | anomaly
  severity: String,     // low | medium | high | critical
  message: String,
  is_read: Boolean,
  created_at: DateTime
}
```

## Mobile App Structure

### Screens
1. **Login** - `/(auth)/login`
2. **Auth Callback** - `/(auth)/callback`
3. **Dashboard** - `/(tabs)/dashboard`
4. **Upload** - `/(tabs)/upload`
5. **Analytics** - `/(tabs)/analytics`
6. **Alerts** - `/(tabs)/alerts`
7. **Admin** - `/(tabs)/admin`

### Navigation
- File-based routing (Expo Router)
- Bottom tab navigation for main screens
- Role-based tab visibility
- Protected routes with authentication

## User Roles & Permissions

### Admin
- Full access to all features
- User management
- Role assignment
- System logs
- Data upload
- All analytics and alerts

### Analyst
- Dashboard access
- Data upload
- Analytics viewing
- Alert management
- No user management

### Viewer
- Dashboard access (read-only)
- Analytics viewing (read-only)
- Alert viewing (read-only)
- No data upload
- No admin access

## ML Model Details

### Risk Prediction
- **Algorithm**: Ensemble (Random Forest + XGBoost)
- **Features**:
  - Hour of day
  - Day of week
  - Month
  - Description length
  - Complaint type (encoded)
  - Location (encoded)
  - Status (encoded)
- **Output**: Risk score 0-100

### Anomaly Detection
- **Algorithm**: Isolation Forest
- **Contamination**: 10%
- **Features**: Same as risk prediction
- **Output**: Binary (anomaly/normal)

## Performance Metrics
- Handles 10,000+ records
- Real-time prediction generation
- Fast API response times (<1s for most endpoints)
- Efficient data processing pipeline

## Security Features
- OAuth 2.0 authentication
- Session-based authorization
- Role-based access control
- Secure cookie storage
- CORS enabled
- Input validation

## Testing
- Mock data generation endpoint
- Test user credentials tracking
- Backend API testing (curl)
- Frontend testing (manual)

## Deployment
- Docker support
- Environment variable configuration
- MongoDB persistence
- Expo tunnel for mobile preview

## Future Enhancements
- [ ] Heatmap visualization (react-native-maps)
- [ ] Advanced charts (trends, forecasting)
- [ ] Real-time notifications
- [ ] Export reports (PDF)
- [ ] Advanced filtering
- [ ] Search functionality
- [ ] Batch operations
- [ ] Model versioning
- [ ] A/B testing for models
- [ ] Performance monitoring
