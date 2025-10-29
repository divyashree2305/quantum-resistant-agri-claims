"""
Epoch Key Manager for Forward-Secure Key Rotation

Manages the lifecycle of Dilithium signing keys on a per-epoch basis.
Private keys are never persisted; only public keys are stored in the database.
"""

from datetime import datetime
from typing import Tuple, Optional
from models.database import EpochKeys, get_session
from key_derivation import load_master_seed, derive_epoch_key


class EpochKeyManager:
    """
    Manages forward-secure Dilithium key lifecycle on epoch basis.
    
    Epochs are identified by date (YYYY-MM-DD format).
    Private keys are derived deterministically from master seed but never stored.
    Retired epochs cannot generate private keys (forward security).
    """
    
    def __init__(self, master_seed: Optional[bytes] = None):
        """
        Initialize Epoch Key Manager.
        
        Args:
            master_seed: Optional master seed. If not provided, loads from environment.
        """
        if master_seed is None:
            self.master_seed = load_master_seed()
        else:
            if len(master_seed) != 32:
                raise ValueError("Master seed must be 32 bytes")
            self.master_seed = master_seed
        
        self.db = None
    
    def _get_db(self):
        """Get database session"""
        if self.db is None:
            self.db = get_session()
        return self.db
    
    def get_current_epoch_id(self) -> str:
        """
        Generate epoch ID from current date.
        
        Returns:
            Epoch ID in YYYY-MM-DD format
        """
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_current_epoch_keypair(self) -> Tuple[bytes, bytes]:
        """
        Get Dilithium keypair for current epoch.
        
        Flow:
        1. Determine current epoch ID
        2. Check if epoch exists in DB and is not retired
        3. If not in DB: derive Dilithium keys, save public key to DB
        4. If retired: raise error (forward security violation)
        5. Return (public_key, private_key)
        
        Returns:
            Tuple of (public_key, private_key) for current epoch
            
        Raises:
            RuntimeError: If current epoch has been retired
            
        Important: Private key is NEVER stored in database
        """
        epoch_id = self.get_current_epoch_id()
        db = self._get_db()
        
        try:
            # Check if epoch already exists in database
            epoch_record = db.query(EpochKeys).filter_by(epoch_id=epoch_id).first()
            
            if epoch_record:
                # Epoch exists - check if retired
                if epoch_record.is_retired:
                    raise RuntimeError(
                        f"Epoch {epoch_id} has been retired. Cannot generate private key. "
                        "This ensures forward security."
                    )
                
                # Epoch exists and is active - derive private key from seed
                public_key, private_key = derive_epoch_key(self.master_seed, epoch_id)
                
                # Verify the public key matches
                if public_key != epoch_record.public_key_ml_dsa:
                    raise RuntimeError(
                        f"Public key mismatch for epoch {epoch_id}. "
                        "This indicates master seed or derivation inconsistency."
                    )
                
                return public_key, private_key
            
            else:
                # Epoch doesn't exist - derive keys and save public key
                public_key, private_key = derive_epoch_key(self.master_seed, epoch_id)
                
                # Save only the public key to database
                new_epoch = EpochKeys(
                    epoch_id=epoch_id,
                    public_key_ml_dsa=public_key,
                    is_retired=False
                )
                
                db.add(new_epoch)
                db.commit()
                
                print(f"✓ Created new epoch: {epoch_id}")
                return public_key, private_key
        
        except Exception as e:
            db.rollback()
            raise
    
    def retire_epoch_key(self, epoch_id: str) -> bool:
        """
        Retire an epoch, preventing future private key derivation.
        Sets is_retired=True in database.
        
        Args:
            epoch_id: Epoch to retire
            
        Returns:
            True if epoch was retired, False if already retired or not found
        """
        db = self._get_db()
        
        try:
            epoch_record = db.query(EpochKeys).filter_by(epoch_id=epoch_id).first()
            
            if not epoch_record:
                print(f"Warning: Epoch {epoch_id} not found in database")
                return False
            
            if epoch_record.is_retired:
                print(f"Info: Epoch {epoch_id} already retired")
                return False
            
            # Retire the epoch
            epoch_record.is_retired = True
            db.commit()
            
            print(f"✓ Retired epoch: {epoch_id}")
            print(f"  Private keys for this epoch can no longer be derived")
            print(f"  Past signatures remain verifiable via stored public key")
            
            return True
        
        except Exception as e:
            db.rollback()
            raise
    
    def get_public_key_for_epoch(self, epoch_id: str) -> Optional[bytes]:
        """
        Retrieve Dilithium public key for any epoch (even retired).
        Used for signature verification of historical records.
        
        Args:
            epoch_id: Epoch to retrieve public key for
            
        Returns:
            Public key bytes, or None if epoch not found
        """
        db = self._get_db()
        
        epoch_record = db.query(EpochKeys).filter_by(epoch_id=epoch_id).first()
        
        if epoch_record:
            return epoch_record.public_key_ml_dsa
        else:
            return None
    
    def list_epochs(self, include_retired: bool = False):
        """
        List all epochs in the database.
        
        Args:
            include_retired: If True, include retired epochs
            
        Returns:
            List of epoch records
        """
        db = self._get_db()
        
        query = db.query(EpochKeys)
        
        if not include_retired:
            query = query.filter_by(is_retired=False)
        
        epochs = query.order_by(EpochKeys.created_at).all()
        
        return epochs
    
    def __del__(self):
        """Clean up database session"""
        if self.db:
            self.db.close()


# Global instance for convenience
_key_manager = None


def get_key_manager(master_seed: Optional[bytes] = None) -> EpochKeyManager:
    """
    Get or create the global EpochKeyManager instance.
    
    Args:
        master_seed: Optional master seed
        
    Returns:
        EpochKeyManager instance
    """
    global _key_manager
    
    if _key_manager is None:
        _key_manager = EpochKeyManager(master_seed=master_seed)
    
    return _key_manager


if __name__ == "__main__":
    print("Epoch Key Manager Test")
    print("=" * 60)
    
    # Initialize manager
    manager = EpochKeyManager()
    
    # Get current epoch keypair
    print(f"\n1. Getting current epoch keypair...")
    public_key, private_key = manager.get_current_epoch_keypair()
    epoch_id = manager.get_current_epoch_id()
    
    print(f"   Epoch ID: {epoch_id}")
    print(f"   Public key size: {len(public_key)} bytes")
    print(f"   Private key size: {len(private_key)} bytes")
    
    # Test retrieving same keypair
    print(f"\n2. Retrieving keypair again (should be same)...")
    public_key2, private_key2 = manager.get_current_epoch_keypair()
    
    if public_key == public_key2 and private_key == private_key2:
        print("   ✓ Keypair is deterministic")
    else:
        print("   ✗ Keypair mismatch!")
    
    # List epochs
    print(f"\n3. Listing epochs...")
    epochs = manager.list_epochs()
    print(f"   Active epochs: {len(epochs)}")
    for epoch in epochs:
        print(f"   - {epoch.epoch_id} (retired: {epoch.is_retired})")
    
    print("\n" + "=" * 60)
    print("Epoch key manager test complete!")

