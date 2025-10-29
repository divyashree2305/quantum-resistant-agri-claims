"""
Checkpoint Module (Phase 3)

Implements Merkle tree construction and checkpoint creation with Dilithium signatures.
Creates periodic snapshots of the log state for integrity verification.
"""

from typing import List, Optional
from models.database import LogEntry, Checkpoint, get_session
from epoch_manager import EpochKeyManager
import crypto


def build_merkle_tree(log_entries: List[LogEntry]) -> bytes:
    """
    Build Merkle tree from log entries and return root hash.
    
    Process:
    1. Extract chain_hash from each LogEntry (use prev_hash field)
    2. Hash all entry hashes to create leaf nodes
    3. Recursively pair and hash nodes until single root
    4. Return merkle_root
    
    Args:
        log_entries: List of LogEntry objects
        
    Returns:
        Merkle root hash (32 bytes)
    """
    if not log_entries:
        return crypto.hash_data(b'EMPTY_TREE')
    
    # Extract hashes from log entries (use prev_hash field)
    hashes = [entry.prev_hash for entry in log_entries]
    
    # Build Merkle tree bottom-up
    while len(hashes) > 1:
        next_level = []
        
        for i in range(0, len(hashes), 2):
            if i + 1 < len(hashes):
                # Pair two hashes
                combined = hashes[i] + hashes[i + 1]
                next_level.append(crypto.hash_data(combined))
            else:
                # Odd number: duplicate last hash
                combined = hashes[i] + hashes[i]
                next_level.append(crypto.hash_data(combined))
        
        hashes = next_level
    
    return hashes[0]


def build_merkle_tree_with_path(log_entries: List[LogEntry], target_entry_id: int) -> tuple[bytes, List[bytes]]:
    """
    Build Merkle tree from log entries while tracking inclusion proof path.
    
    Process:
    1. Extract chain_hash from each LogEntry (use prev_hash field)
    2. Build Merkle tree bottom-up
    3. Track sibling hashes at each level for target entry
    4. Return merkle_root and proof path
    
    Args:
        log_entries: List of LogEntry objects
        target_entry_id: ID of entry to generate proof for
        
    Returns:
        Tuple of (merkle_root, merkle_path)
        - merkle_root: Root hash (32 bytes)
        - merkle_path: List of sibling hashes for each level (from leaf to root)
    """
    if not log_entries:
        return crypto.hash_data(b'EMPTY_TREE'), []
    
    # Find index of target entry
    target_index = None
    for i, entry in enumerate(log_entries):
        if entry.id == target_entry_id:
            target_index = i
            break
    
    if target_index is None:
        raise ValueError(f"Target entry {target_entry_id} not found in log entries")
    
    # Extract hashes from log entries (use prev_hash field)
    hashes = [entry.prev_hash for entry in log_entries]
    merkle_path = []
    current_level_hashes = hashes.copy()
    current_target_index = target_index
    
    # Build Merkle tree bottom-up while tracking path
    while len(current_level_hashes) > 1:
        next_level = []
        next_target_index = None
        
        for i in range(0, len(current_level_hashes), 2):
            if i + 1 < len(current_level_hashes):
                # Pair two hashes
                combined = current_level_hashes[i] + current_level_hashes[i + 1]
                next_level.append(crypto.hash_data(combined))
                
                # Track sibling for proof path
                if i == current_target_index:
                    # Target is left child, sibling is right
                    merkle_path.append(current_level_hashes[i + 1])
                    next_target_index = len(next_level) - 1
                elif i + 1 == current_target_index:
                    # Target is right child, sibling is left
                    merkle_path.append(current_level_hashes[i])
                    next_target_index = len(next_level) - 1
            else:
                # Odd number: duplicate last hash
                combined = current_level_hashes[i] + current_level_hashes[i]
                next_level.append(crypto.hash_data(combined))
                
                # Track sibling for proof path (self as sibling)
                if i == current_target_index:
                    merkle_path.append(current_level_hashes[i])
                    next_target_index = len(next_level) - 1
        
        current_level_hashes = next_level
        current_target_index = next_target_index
    
    merkle_root = current_level_hashes[0] if current_level_hashes else crypto.hash_data(b'EMPTY_TREE')
    
    return merkle_root, merkle_path


def get_last_checkpoint() -> Optional[Checkpoint]:
    """Get the most recent checkpoint"""
    db = get_session()
    
    try:
        last_checkpoint = db.query(Checkpoint).order_by(Checkpoint.id.desc()).first()
        return last_checkpoint
    finally:
        db.close()


def get_entries_since_checkpoint(last_checkpoint_id: int) -> List[LogEntry]:
    """
    Get log entries created since the last checkpoint.
    
    Args:
        last_checkpoint_id: Last checkpoint's end ID
        
    Returns:
        List of LogEntry objects
    """
    db = get_session()
    
    try:
        entries = db.query(LogEntry)\
            .filter(LogEntry.id > last_checkpoint_id)\
            .order_by(LogEntry.id.asc())\
            .all()
        return entries
    finally:
        db.close()


def compute_checkpoint_hash(checkpoint: Checkpoint) -> bytes:
    """
    Compute hash of checkpoint data for chain linkage.
    
    Args:
        checkpoint: Checkpoint object
        
    Returns:
        Hash of checkpoint data
    """
    # Combine checkpoint fields for hashing
    data_parts = [
        checkpoint.merkle_root,
        checkpoint.entries_range.encode('utf-8'),
        checkpoint.prev_checkpoint_hash,
        checkpoint.signer_id.encode('utf-8') if checkpoint.signer_id else b'',
        checkpoint.created_at.isoformat().encode('utf-8')
    ]
    
    combined = b''.join(data_parts)
    return crypto.hash_data(combined)


def generate_checkpoint() -> Checkpoint:
    """
    Generate a signed checkpoint for recent log entries.
    
    Process:
    1. Query LogEntry records since last checkpoint
    2. Build Merkle tree from entries to get merkle_root
    3. Get current epoch keypair from EpochKeyManager
    4. Sign merkle_root with Dilithium private key
    5. Save Checkpoint with signature and metadata
    
    Returns:
        Created Checkpoint database object
    """
    db = get_session()
    
    try:
        # Get last checkpoint
        last_checkpoint = get_last_checkpoint()
        
        if last_checkpoint:
            # Extract the maximum ID from last checkpoint's range
            # Format: "1-100" or "101-200"
            range_parts = last_checkpoint.entries_range.split('-')
            last_max_id = int(range_parts[-1])
        else:
            # No previous checkpoint
            last_max_id = 0
        
        # Get entries since last checkpoint
        entries = get_entries_since_checkpoint(last_max_id)
        
        if not entries:
            raise ValueError("No new log entries to checkpoint")
        
        # Build Merkle tree
        merkle_root = build_merkle_tree(entries)
        
        # Get current epoch keypair from Phase 2
        manager = EpochKeyManager()
        epoch_id = manager.get_current_epoch_id()
        public_key, private_key = manager.get_current_epoch_keypair()
        
        # Sign the Merkle root
        signature = crypto.sign_message(merkle_root, private_key)
        
        # Compute previous checkpoint hash
        if last_checkpoint:
            prev_checkpoint_hash = compute_checkpoint_hash(last_checkpoint)
        else:
            # Genesis hash for first checkpoint
            prev_checkpoint_hash = crypto.hash_data(b"CHECKPOINT_GENESIS")
        
        # Determine entry range
        entry_min = entries[0].id
        entry_max = entries[-1].id
        entries_range = f"{entry_min}-{entry_max}"
        
        # Create checkpoint
        checkpoint = Checkpoint(
            merkle_root=merkle_root,
            entries_range=entries_range,
            prev_checkpoint_hash=prev_checkpoint_hash,
            signer_id=epoch_id,
            signer_ml_dsa_sig=signature
        )
        
        db.add(checkpoint)
        db.commit()
        db.refresh(checkpoint)
        
        print(f"✓ Created checkpoint: ID={checkpoint.id}, Range={entries_range}, Epoch={epoch_id}")
        
        return checkpoint
    
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to generate checkpoint: {e}")
    
    finally:
        db.close()


def verify_checkpoint_signature(checkpoint: Checkpoint) -> bool:
    """
    Verify Dilithium signature on a checkpoint.
    Uses stored public key from EpochKeys table.
    
    Args:
        checkpoint: Checkpoint to verify
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Get public key for the epoch from Phase 2
        manager = EpochKeyManager()
        public_key = manager.get_public_key_for_epoch(checkpoint.signer_id)
        
        if not public_key:
            print(f"Public key not found for epoch: {checkpoint.signer_id}")
            return False
        
        # Verify signature
        is_valid = crypto.verify_signature(
            checkpoint.merkle_root,
            checkpoint.signer_ml_dsa_sig,
            public_key
        )
        
        return is_valid
    
    except Exception as e:
        print(f"Checkpoint verification error: {e}")
        return False


if __name__ == "__main__":
    # Test checkpoint generation
    print("Checkpoint Module Test")
    print("=" * 60)
    
    print("\n1. Creating checkpoint for recent log entries...")
    
    try:
        checkpoint = generate_checkpoint()
        print(f"✓ Checkpoint created:")
        print(f"   ID: {checkpoint.id}")
        print(f"   Range: {checkpoint.entries_range}")
        print(f"   Epoch: {checkpoint.signer_id}")
        print(f"   Merkle Root: {checkpoint.merkle_root.hex()[:16]}...")
        
        print("\n2. Verifying checkpoint signature...")
        if verify_checkpoint_signature(checkpoint):
            print("✓ Checkpoint signature is valid")
        else:
            print("✗ Checkpoint signature is invalid")
        
    except ValueError as e:
        print(f"Note: {e}")
        print("   Add some log entries first using append_log.py")
    
    print("\n" + "=" * 60)
    print("Checkpoint module test complete!")

