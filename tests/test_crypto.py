"""
Basic tests for post-quantum cryptographic operations.

Tests SHA3 hashing, Dilithium signatures, Kyber KEM, and Merkle tree generation.
"""

try:
    import pytest
except ImportError:
    pass  # pytest not available, but not needed for main execution

import crypto


def test_hash_data():
    """Test SHA3-256 hashing"""
    test_data = b"test message"
    hash_result = crypto.hash_data(test_data)
    
    assert hash_result is not None
    assert len(hash_result) == 32  # SHA3-256 produces 32 bytes
    assert isinstance(hash_result, bytes)
    
    # Same input should produce same hash
    hash_result2 = crypto.hash_data(test_data)
    assert hash_result == hash_result2


def test_hash_chain():
    """Test hash chaining for tamper-evident logging"""
    prev_hash = crypto.hash_data(b"previous")
    current_data = b"current"
    
    chain_hash = crypto.hash_chain(prev_hash, current_data)
    
    assert chain_hash is not None
    assert len(chain_hash) == 32
    assert chain_hash != prev_hash
    assert chain_hash != crypto.hash_data(current_data)


def test_dilithium_keypair():
    """Test Dilithium keypair generation"""
    public_key, private_key = crypto.generate_dilithium_keypair()
    
    assert public_key is not None
    assert private_key is not None
    assert len(public_key) > 0
    assert len(private_key) > 0
    assert public_key != private_key


def test_dilithium_sign_verify():
    """Test Dilithium signature creation and verification"""
    public_key, private_key = crypto.generate_dilithium_keypair()
    message = b"test message for signing"
    
    signature = crypto.sign_message(message, private_key)
    
    assert signature is not None
    assert len(signature) > 0
    
    # Verify the signature
    is_valid = crypto.verify_signature(message, signature, public_key)
    assert is_valid
    
    # Test with wrong message
    wrong_message = b"wrong message"
    is_invalid = crypto.verify_signature(wrong_message, signature, public_key)
    assert not is_invalid


def test_kyber_keypair():
    """Test Kyber keypair generation"""
    public_key, private_key = crypto.generate_kyber_keypair()
    
    assert public_key is not None
    assert private_key is not None
    assert len(public_key) > 0
    assert len(private_key) > 0


def test_kyber_encapsulate_decapsulate():
    """Test Kyber key encapsulation and decapsulation"""
    public_key, private_key = crypto.generate_kyber_keypair()
    
    # Encapsulate (returns shared_secret, ciphertext)
    shared_secret, ciphertext = crypto.kyber_encapsulate(public_key)
    
    assert ciphertext is not None
    assert shared_secret is not None
    assert len(ciphertext) > 0
    assert len(shared_secret) > 0
    
    # Decapsulate - pass ciphertext first, then private_key
    recovered_secret = crypto.kyber_decapsulate(ciphertext, private_key)
    
    assert recovered_secret is not None
    assert len(recovered_secret) > 0
    assert shared_secret == recovered_secret


def test_merkle_root():
    """Test Merkle tree root generation"""
    test_items = [b"item1", b"item2", b"item3", b"item4"]
    
    merkle_root = crypto.generate_merkle_root(test_items)
    
    assert merkle_root is not None
    assert len(merkle_root) == 32  # SHA3-256 output
    
    # Empty list should return hash of empty bytes
    empty_root = crypto.generate_merkle_root([])
    assert empty_root == crypto.hash_data(b'')
    
    # Single item should return hash of that item
    single_root = crypto.generate_merkle_root([b"single"])
    assert single_root == crypto.hash_data(b"single")


def test_crypto_info():
    """Test crypto info function"""
    info = crypto.get_crypto_info()
    
    assert "hashing" in info
    assert "dilithium" in info
    assert "kyber" in info
    assert info["quantum_resistant"] is True


if __name__ == "__main__":
    # Run tests
    print("Running crypto module tests...")
    print("=" * 60)
    
    try:
        test_hash_data()
        print("✓ Hash data test passed")
        
        test_hash_chain()
        print("✓ Hash chain test passed")
        
        test_dilithium_keypair()
        print("✓ Dilithium keypair test passed")
        
        test_dilithium_sign_verify()
        print("✓ Dilithium sign/verify test passed")
        
        test_kyber_keypair()
        print("✓ Kyber keypair test passed")
        
        test_kyber_encapsulate_decapsulate()
        print("✓ Kyber encapsulate/decapsulate test passed")
        
        test_merkle_root()
        print("✓ Merkle root test passed")
        
        test_crypto_info()
        print("✓ Crypto info test passed")
        
        print("\n" + "=" * 60)
        print("All tests passed successfully!")
        
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        raise
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        raise

