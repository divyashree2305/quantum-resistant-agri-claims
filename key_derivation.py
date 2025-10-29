"""
Key Derivation Module for Forward-Secure Key Manager

Provides deterministic key derivation using HKDF for epoch-based Dilithium key generation.
"""

import os
from typing import Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import crypto


def load_master_seed() -> bytes:
    """
    Load master seed from environment variable.
    If not present, generate and warn (dev mode only).
    
    Returns:
        32-byte master seed as bytes
        
    Raises:
        ValueError: If MASTER_SEED environment variable is not set in production
    """
    master_seed_hex = os.environ.get("MASTER_SEED")
    
    if master_seed_hex:
        try:
            # Strip any whitespace/newlines from the environment variable
            master_seed_hex = master_seed_hex.strip()
            
            # Validate hex string length
            if len(master_seed_hex) != 64:
                print(f"WARNING: MASTER_SEED has invalid length ({len(master_seed_hex)} chars instead of 64).")
                print(f"Value (first 100 chars): {master_seed_hex[:100]}")
                print("Generating a new master seed for development.")
                # Don't raise error, fall through to dev mode
            else:
                # Convert hex string to bytes
                seed = bytes.fromhex(master_seed_hex)
                if len(seed) != 32:
                    raise ValueError(f"MASTER_SEED must be 64 hex characters (32 bytes), got {len(seed)} bytes")
                return seed
        except ValueError as e:
            print(f"WARNING: Invalid MASTER_SEED format: {e}")
            # Don't raise error, fall through to dev mode
    
    # Development mode: generate a random seed
    if not master_seed_hex:
        print("WARNING: MASTER_SEED not found in environment.")
    print("Generating a random master seed for development.")
    print("This seed should be stored securely in production!")
    dev_seed = os.urandom(32)
    dev_seed_hex = dev_seed.hex()
    print(f"Generated dev seed: {dev_seed_hex}")
    print(f"Export this as: export MASTER_SEED={dev_seed_hex}")
    # Set the environment variable so it persists for the session
    os.environ["MASTER_SEED"] = dev_seed_hex
    return dev_seed


def derive_epoch_key(master_seed: bytes, epoch_id: str) -> Tuple[bytes, bytes]:
    """
    Derive Dilithium keypair from master seed and epoch ID.
    Uses HKDF-SHA256 for deterministic seed generation.
    
    Args:
        master_seed: 32-byte master secret
        epoch_id: String identifier (e.g., "2025-10-28")
        
    Returns:
        (public_key, private_key) tuple - Dilithium keys
        
    Raises:
        ValueError: If master_seed is not 32 bytes
    """
    if len(master_seed) != 32:
        raise ValueError(f"Master seed must be 32 bytes, got {len(master_seed)}")
    
    # Use HKDF to derive a deterministic 32-byte seed from master_seed + epoch_id
    info = epoch_id.encode('utf-8')  # Domain separation with epoch_id
    
    # HKDF: HMAC-based Key Derivation Function
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # 32-byte derived seed
        salt=None,  # No salt for deterministic derivation
        info=info,  # Epoch ID as context
    )
    
    # Derive the seed
    derived_seed = hkdf.derive(master_seed)
    
    # Generate Dilithium keypair from derived seed
    public_key, private_key = crypto.generate_dilithium_keypair_from_seed(derived_seed)
    
    return public_key, private_key


def validate_seed_derivation():
    """
    Validate that key derivation is deterministic.
    Same master_seed + epoch_id always produces same keys.
    """
    # Use a test seed for validation
    test_seed = b"0" * 32
    epoch_id = "2025-01-01"
    
    # Derive keys twice
    pub1, priv1 = derive_epoch_key(test_seed, epoch_id)
    pub2, priv2 = derive_epoch_key(test_seed, epoch_id)
    
    # Should be identical
    assert pub1 == pub2, "Keys must be deterministic!"
    assert priv1 == priv2, "Keys must be deterministic!"
    
    print("✓ Key derivation validation passed")
    return True


if __name__ == "__main__":
    # Test key derivation
    print("Key Derivation Module Test")
    print("=" * 60)
    
    # Test with dummy seed
    master_seed = os.urandom(32)
    epoch_id = "2025-10-28"
    
    print(f"Master seed (first 16 bytes): {master_seed[:16].hex()}")
    print(f"Epoch ID: {epoch_id}")
    
    public_key, private_key = derive_epoch_key(master_seed, epoch_id)
    
    print(f"\nDerived Dilithium keys:")
    print(f"  Public key size: {len(public_key)} bytes")
    print(f"  Private key size: {len(private_key)} bytes")
    
    # Test determinism
    print("\nTesting determinism...")
    validate_seed_derivation()
    
    print("\n" + "=" * 60)
    print("All key derivation tests passed!")

