#!/usr/bin/env python3
"""
Simple test script to verify the authentication system is working.
Run this after setting up the database to test user registration and login.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    # Test data
    test_user = {
        "username": "testuser",
        "password": "TestPass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            data = response.json()
            print(f"   User ID: {data['user_id']}")
            print(f"   Username: {data['username']}")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\nTesting user login...")
    
    login_data = {
        "username": "testuser",
        "password": "TestPass123",
        "remember": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Login successful!")
            data = response.json()
            print(f"   Username: {data['user']['username']}")
            print(f"   Session ID: {data['session_id']}")
            return data['session_id']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_profile(session_id):
    """Test getting user profile"""
    if not session_id:
        print("\nSkipping profile test (no session)")
        return
        
    print("\nTesting profile access...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/profile",
            headers={
                "X-Session-ID": session_id,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print("✅ Profile access successful!")
            data = response.json()
            print(f"   Username: {data['username']}")
            print(f"   Created: {data['created_at']}")
        else:
            print(f"❌ Profile access failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Profile access error: {e}")

def test_logout(session_id):
    """Test user logout"""
    if not session_id:
        print("\nSkipping logout test (no session)")
        return
        
    print("\nTesting logout...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/logout",
            json={"session_id": session_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Logout successful!")
        else:
            print(f"❌ Logout failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Logout error: {e}")

def main():
    """Run all tests"""
    print("🧪 MoreAI Authentication System Test")
    print("=" * 40)
    
    # Test registration
    if test_registration():
        # Test login
        session_id = test_login()
        
        # Test profile access
        test_profile(session_id)
        
        # Test logout
        test_logout(session_id)
    
    print("\n" + "=" * 40)
    print("🎯 Test completed!")
    
    print("\n📝 To test manually:")
    print("1. Open http://localhost:8000/register")
    print("2. Create a new account")
    print("3. Go to http://localhost:8000/login")
    print("4. Sign in with your credentials")
    print("5. You'll be redirected to the main page")

if __name__ == "__main__":
    main() 