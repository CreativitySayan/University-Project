#!/usr/bin/env python3
"""
CyberGuard Pro Backend API Testing Suite
Tests all backend endpoints with proper authentication
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://risk-predict-ai-1.preview.emergentagent.com/api"
SESSION_TOKEN = "test_session_1775404646600"  # Generated admin session token

# Headers for authenticated requests
AUTH_HEADERS = {
    "Authorization": f"Bearer {SESSION_TOKEN}",
    "Content-Type": "application/json"
}

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n=== Testing Authentication Endpoints ===")
    
    # Test /api/auth/me with valid token
    print("1. Testing GET /api/auth/me with valid token...")
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=AUTH_HEADERS)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   User: {user_data.get('name')} ({user_data.get('role')})")
            print("   ✅ Auth endpoint working")
            return True
        else:
            print(f"   ❌ Auth failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Auth error: {str(e)}")
        return False

def test_protected_endpoints_without_auth():
    """Test that protected endpoints return 401 without auth"""
    print("\n=== Testing Protected Endpoints Without Auth ===")
    
    endpoints = [
        "/dashboard/stats",
        "/complaints", 
        "/alerts",
        "/admin/users"
    ]
    
    all_protected = True
    for endpoint in endpoints:
        print(f"Testing {endpoint} without auth...")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 401:
                print(f"   ✅ {endpoint} properly protected (401)")
            else:
                print(f"   ❌ {endpoint} not protected (got {response.status_code})")
                all_protected = False
        except Exception as e:
            print(f"   ❌ Error testing {endpoint}: {str(e)}")
            all_protected = False
    
    return all_protected

def test_mock_data_generation():
    """Test mock data generation endpoint"""
    print("\n=== Testing Mock Data Generation ===")
    
    print("Testing POST /api/generate-mock-data?count=50...")
    try:
        response = requests.post(
            f"{BASE_URL}/generate-mock-data?count=50",
            headers=AUTH_HEADERS
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Total records: {data.get('total_records')}")
            print(f"   Complaints created: {data.get('complaints_created')}")
            print(f"   Predictions created: {data.get('predictions_created')}")
            print(f"   Alerts created: {data.get('alerts_created')}")
            print("   ✅ Mock data generation working")
            return True
        else:
            print(f"   ❌ Mock data generation failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Mock data generation error: {str(e)}")
        return False

def test_dashboard_stats():
    """Test dashboard statistics endpoint"""
    print("\n=== Testing Dashboard Stats ===")
    
    print("Testing GET /api/dashboard/stats...")
    try:
        response = requests.get(f"{BASE_URL}/dashboard/stats", headers=AUTH_HEADERS)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"   Total complaints: {stats.get('total_complaints')}")
            print(f"   High risk count: {stats.get('high_risk_count')}")
            print(f"   Anomaly count: {stats.get('anomaly_count')}")
            print(f"   Alerts count: {stats.get('alerts_count')}")
            print(f"   Risk distribution: {stats.get('risk_distribution')}")
            print(f"   Category counts: {stats.get('category_counts')}")
            print("   ✅ Dashboard stats working")
            return True
        else:
            print(f"   ❌ Dashboard stats failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Dashboard stats error: {str(e)}")
        return False

def test_complaints_endpoint():
    """Test complaints endpoint with filters"""
    print("\n=== Testing Complaints Endpoint ===")
    
    # Test basic complaints endpoint
    print("1. Testing GET /api/complaints...")
    try:
        response = requests.get(f"{BASE_URL}/complaints", headers=AUTH_HEADERS)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            complaints = response.json()
            print(f"   Retrieved {len(complaints)} complaints")
            
            # Check if predictions are attached
            if complaints and len(complaints) > 0:
                first_complaint = complaints[0]
                if 'prediction' in first_complaint:
                    print("   ✅ Predictions attached to complaints")
                else:
                    print("   ⚠️ No predictions attached to complaints")
            
            print("   ✅ Basic complaints endpoint working")
        else:
            print(f"   ❌ Complaints endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Complaints endpoint error: {str(e)}")
        return False
    
    # Test with risk level filters
    risk_levels = ["High", "Low", "Medium"]
    for risk_level in risk_levels:
        print(f"2. Testing GET /api/complaints?risk_level={risk_level}...")
        try:
            response = requests.get(
                f"{BASE_URL}/complaints?risk_level={risk_level}",
                headers=AUTH_HEADERS
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                filtered_complaints = response.json()
                print(f"   Retrieved {len(filtered_complaints)} {risk_level} risk complaints")
                print(f"   ✅ Risk level filter {risk_level} working")
            else:
                print(f"   ❌ Risk level filter {risk_level} failed: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Risk level filter {risk_level} error: {str(e)}")
            return False
    
    return True

def test_alerts_endpoint():
    """Test alerts endpoints"""
    print("\n=== Testing Alerts Endpoints ===")
    
    # Test get alerts
    print("1. Testing GET /api/alerts...")
    try:
        response = requests.get(f"{BASE_URL}/alerts", headers=AUTH_HEADERS)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            alerts = response.json()
            print(f"   Retrieved {len(alerts)} alerts")
            
            # Check for unread alerts
            unread_alerts = [alert for alert in alerts if not alert.get('is_read', True)]
            print(f"   Unread alerts: {len(unread_alerts)}")
            
            # Test marking alert as read if we have alerts
            if alerts and len(alerts) > 0:
                alert_id = alerts[0].get('alert_id')
                if alert_id:
                    print(f"2. Testing PATCH /api/alerts/{alert_id}/read...")
                    try:
                        patch_response = requests.patch(
                            f"{BASE_URL}/alerts/{alert_id}/read",
                            headers=AUTH_HEADERS
                        )
                        print(f"   Status: {patch_response.status_code}")
                        
                        if patch_response.status_code == 200:
                            print("   ✅ Alert mark as read working")
                        else:
                            print(f"   ❌ Alert mark as read failed: {patch_response.text}")
                            return False
                    except Exception as e:
                        print(f"   ❌ Alert mark as read error: {str(e)}")
                        return False
            
            print("   ✅ Alerts endpoints working")
            return True
        else:
            print(f"   ❌ Alerts endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Alerts endpoint error: {str(e)}")
        return False

def test_admin_endpoints():
    """Test admin-only endpoints"""
    print("\n=== Testing Admin Endpoints ===")
    
    # Test get users
    print("1. Testing GET /api/admin/users...")
    try:
        response = requests.get(f"{BASE_URL}/admin/users", headers=AUTH_HEADERS)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"   Retrieved {len(users)} users")
            
            # Test update user role if we have users
            if users and len(users) > 0:
                user_id = users[0].get('user_id')
                if user_id:
                    print(f"2. Testing PATCH /api/admin/users/{user_id}/role?role=analyst...")
                    try:
                        patch_response = requests.patch(
                            f"{BASE_URL}/admin/users/{user_id}/role?role=analyst",
                            headers=AUTH_HEADERS
                        )
                        print(f"   Status: {patch_response.status_code}")
                        
                        if patch_response.status_code == 200:
                            print("   ✅ User role update working")
                        else:
                            print(f"   ❌ User role update failed: {patch_response.text}")
                            return False
                    except Exception as e:
                        print(f"   ❌ User role update error: {str(e)}")
                        return False
            
            print("   ✅ Admin users endpoint working")
        else:
            print(f"   ❌ Admin users endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Admin users endpoint error: {str(e)}")
        return False
    
    # Test get logs
    print("3. Testing GET /api/admin/logs...")
    try:
        response = requests.get(f"{BASE_URL}/admin/logs", headers=AUTH_HEADERS)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            logs = response.json()
            print(f"   Retrieved {len(logs)} log entries")
            print("   ✅ Admin logs endpoint working")
            return True
        else:
            print(f"   ❌ Admin logs endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Admin logs endpoint error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting CyberGuard Pro Backend API Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Session Token: {SESSION_TOKEN}")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Authentication", test_auth_endpoints()))
    test_results.append(("Protected Endpoints", test_protected_endpoints_without_auth()))
    test_results.append(("Mock Data Generation", test_mock_data_generation()))
    test_results.append(("Dashboard Stats", test_dashboard_stats()))
    test_results.append(("Complaints Endpoint", test_complaints_endpoint()))
    test_results.append(("Alerts Endpoints", test_alerts_endpoint()))
    test_results.append(("Admin Endpoints", test_admin_endpoints()))
    
    # Summary
    print("\n" + "="*60)
    print("🏁 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️ {failed} test(s) failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)