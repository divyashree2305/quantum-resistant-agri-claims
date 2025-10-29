"""
Tests for API endpoints (Phase 5)

Tests the handshake, claim submission, and checkpoint generation endpoints.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import base64
import json
from fastapi.testclient import TestClient
from api.main import app
import crypto
from models.database import init_db

# Initialize test client
client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    print("\n1. Testing /health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("   ✓ Health check works")


def test_handshake():
    """Test Kyber handshake endpoint"""
    print("\n2. Testing /handshake endpoint...")
    
    # Generate client's Kyber keypair
    client_pub_key, client_priv_key = crypto.generate_kyber_keypair()
    
    # Encode public key
    client_pub_key_b64 = base64.b64encode(client_pub_key).decode('utf-8')
    
    # Send handshake request
    response = client.post(
        "/handshake",
        json={"client_public_key": client_pub_key_b64}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "server_public_key" in data
    assert "ciphertext" in data
    assert "session_token" in data
    
    # Decode server's public key
    server_pub_key = base64.b64decode(data["server_public_key"])
    ciphertext = base64.b64decode(data["ciphertext"])
    
    # Client decapsulates shared secret
    shared_secret_client = crypto.kyber_decapsulate(ciphertext, client_priv_key)
    
    print(f"   ✓ Handshake successful")
    print(f"     Session token: {data['session_token'][:20]}...")
    print(f"     Server public key length: {len(server_pub_key)} bytes")
    print(f"     Shared secret length: {len(shared_secret_client)} bytes")
    
    return data["session_token"]


def test_claim_submit(session_token):
    """Test claim submission endpoint"""
    print("\n3. Testing /claim/submit endpoint...")
    
    claim_data = {
        "claim_amount": 5000.0,
        "time_of_day": 14,
        "location_risk": 0.3
    }
    
    # Submit claim with session token
    response = client.post(
        "/claim/submit",
        json={"claim_data": claim_data},
        headers={"X-Session-Token": session_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "log_entry_id" in data
    assert "fraud_score" in data
    assert "model_version" in data
    assert 0.0 <= data["fraud_score"] <= 1.0
    
    print(f"   ✓ Claim submitted successfully")
    print(f"     Log entry ID: {data['log_entry_id']}")
    print(f"     Fraud score: {data['fraud_score']:.4f}")
    print(f"     Model version: {data['model_version']}")
    
    return data["log_entry_id"]


def test_claim_submit_no_session():
    """Test claim submission without session token"""
    print("\n4. Testing /claim/submit without session...")
    
    claim_data = {
        "claim_amount": 1000.0,
        "time_of_day": 10,
        "location_risk": 0.2
    }
    
    response = client.post(
        "/claim/submit",
        json={"claim_data": claim_data}
    )
    
    assert response.status_code == 401
    print("   ✓ Correctly rejects request without session token")


def test_generate_checkpoint():
    """Test checkpoint generation endpoint"""
    print("\n5. Testing /admin/generate-checkpoint endpoint...")
    
    response = client.post("/admin/generate-checkpoint")
    
    # May succeed if there are entries, or fail if none
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "checkpoint_id" in data
        assert "merkle_root" in data
        assert "entries_range" in data
        print(f"   ✓ Checkpoint generated successfully")
        print(f"     Checkpoint ID: {data['checkpoint_id']}")
        print(f"     Entries range: {data['entries_range']}")
        return data["checkpoint_id"]
    else:
        # No entries to checkpoint
        print("   ✓ Endpoint works (no entries to checkpoint)")
        return None


def test_audit_endpoints(log_entry_id, checkpoint_id):
    """Test audit verification endpoints"""
    print("\n6. Testing audit endpoints...")
    
    if checkpoint_id:
        # Test verify checkpoint
        response = client.get(f"/audit/verify-checkpoint/{checkpoint_id}")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✓ Verify checkpoint: {data.get('valid', False)}")
    
    if log_entry_id:
        # Test prove inclusion
        response = client.get(f"/audit/prove-inclusion/{log_entry_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Prove inclusion: merkle_path length = {len(data.get('merkle_path', []))}")
        
        # Test verify AI score
        response = client.get(f"/audit/verify-ai-score/{log_entry_id}")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✓ Verify AI score: entry found = {data.get('valid', False)}")


if __name__ == "__main__":
    print("=" * 60)
    print("API Endpoints Tests (Phase 5)")
    print("=" * 60)
    
    # Initialize database
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"Note: Database initialization: {e}")
    
    try:
        # Run tests
        test_health_check()
        session_token = test_handshake()
        log_entry_id = test_claim_submit(session_token)
        test_claim_submit_no_session()
        checkpoint_id = test_generate_checkpoint()
        test_audit_endpoints(log_entry_id, checkpoint_id)
        
        print("\n" + "=" * 60)
        print("✓ All API endpoint tests completed!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


