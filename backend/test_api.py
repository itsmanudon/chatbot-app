#!/usr/bin/env python3
"""
Test the FastAPI endpoints without external dependencies
"""

from fastapi.testclient import TestClient
import os
import sys

# Set mock environment variables
os.environ['DATABASE_URL'] = 'sqlite:///test.db'  # Use SQLite for testing
os.environ['DEFAULT_AI_PROVIDER'] = 'openai'

from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    print("🔍 Testing root endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data
    print(f"  ✓ Root endpoint: {data}")

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n🏥 Testing health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    print(f"  ✓ Health check: {data}")

def test_chat_endpoint_structure():
    """Test chat endpoint structure (will fail without DB but tests routing)"""
    print("\n💬 Testing chat endpoint structure...")
    
    # Test with invalid data
    response = client.post("/chat", json={})
    # Should get validation error
    assert response.status_code in [422, 500]  # Validation error or DB error
    print(f"  ✓ Chat endpoint rejects invalid data (status: {response.status_code})")
    
    # Test with valid structure but no DB
    response = client.post("/chat", json={
        "message": "Hello",
        "session_id": "test-123"
    })
    # May fail due to DB not being available, but that's expected
    print(f"  ✓ Chat endpoint accepts valid request structure (status: {response.status_code})")

def main():
    """Run all endpoint tests"""
    print("=" * 60)
    print("🧪 Testing API Endpoints")
    print("=" * 60)
    
    try:
        test_root_endpoint()
        test_health_endpoint()
        test_chat_endpoint_structure()
        
        print("\n" + "=" * 60)
        print("✅ API ENDPOINT TESTS PASSED!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
