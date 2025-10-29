"""
Log Verification Module (Phase 3)

Provides functions to verify integrity of tamper-evident logs.
Detects any modifications to log entries or checkpoints.
"""

from typing import Optional
from models.database import LogEntry, Checkpoint, get_session
import append_log
import crypto


def verify_log_chain(start_id: int = 1, end_id: Optional[int] = None) -> tuple[bool, list]:
    """
    Verify hash chain integrity from start to end.
    Detects any tampering in the log entries.
    
    Args:
        start_id: Starting log entry ID (default: 1)
        end_id: Ending log entry ID (None = all entries)
        
    Returns:
        (is_valid, issues) tuple
        - is_valid: True if chain is intact
        - issues: List of discovered issues
    """
    db = get_session()
    issues = []
    
    try:
        # Get entries to verify
        query = db.query(LogEntry).filter(LogEntry.id >= start_id)
        if end_id:
            query = query.filter(LogEntry.id <= end_id)
        
        entries = query.order_by(LogEntry.id.asc()).all()
        
        if len(entries) < 2:
            return True, ["Not enough entries to verify chain"]
        
        # Start with genesis hash
        prev_hash = crypto.hash_data(b"GENESIS")
        
        for i, entry in enumerate(entries):
            if i == 0:
                # First entry: compute chain hash from genesis
                payload_hash = entry.payload_hash
                timestamp = entry.timestamp_local
                expected_hash = append_log.compute_chain_hash(
                    prev_hash,  # genesis hash
                    payload_hash,
                    timestamp
                )
                actual_hash = entry.prev_hash
            else:
                # Subsequent entries: compute chain hash from previous entry
                prev_entry = entries[i - 1]
                payload_hash = entry.payload_hash
                timestamp = entry.timestamp_local
                expected_hash = append_log.compute_chain_hash(
                    prev_entry.prev_hash,
                    payload_hash,
                    timestamp
                )
                actual_hash = entry.prev_hash
            
            # Verify chain hash
            if actual_hash != expected_hash:
                issues.append(
                    f"Entry {entry.id}: Chain hash mismatch.\n"
                    f"  Expected: {expected_hash.hex()[:16]}...\n"
                    f"  Actual: {actual_hash.hex()[:16]}..."
                )
        
        is_valid = len(issues) == 0
        
        if is_valid:
            issues.append("✓ All chain hashes verified")
        
        return is_valid, issues
    
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
    from checkpoint import verify_checkpoint_signature as _verify
    return _verify(checkpoint)


def verify_checkpoint_merkle_tree(checkpoint: Checkpoint) -> tuple[bool, Optional[str]]:
    """
    Verify that checkpoint's Merkle root matches the actual log entries.
    
    Args:
        checkpoint: Checkpoint to verify
        
    Returns:
        (is_valid, issue) tuple
    """
    db = get_session()
    
    try:
        # Parse entry range
        range_parts = checkpoint.entries_range.split('-')
        min_id = int(range_parts[0])
        max_id = int(range_parts[-1])
        
        # Get entries in range
        entries = db.query(LogEntry)\
            .filter(LogEntry.id >= min_id, LogEntry.id <= max_id)\
            .order_by(LogEntry.id.asc())\
            .all()
        
        if not entries:
            return False, "No entries found in checkpoint range"
        
        # Rebuild Merkle tree
        from checkpoint import build_merkle_tree
        computed_root = build_merkle_tree(entries)
        
        # Compare with checkpoint's Merkle root
        if computed_root != checkpoint.merkle_root:
            return False, f"Merkle root mismatch.\n  Computed: {computed_root.hex()[:16]}...\n  Stored: {checkpoint.merkle_root.hex()[:16]}..."
        
        return True, None
    
    finally:
        db.close()


def full_verification(start_id: int = 1) -> dict:
    """
    Perform full verification of log integrity.
    Checks hash chains, checkpoint signatures, and Merkle trees.
    
    Args:
        start_id: Starting log entry ID
        
    Returns:
        Dictionary with verification results
    """
    results = {
        "chain_valid": False,
        "checkpoints_valid": [],
        "merkle_valid": [],
        "issues": []
    }
    
    # Verify hash chain
    chain_valid, issues = verify_log_chain(start_id)
    results["chain_valid"] = chain_valid
    results["issues"].extend(issues)
    
    # Get all checkpoints
    db = get_session()
    try:
        checkpoints = db.query(Checkpoint).order_by(Checkpoint.id.asc()).all()
        
        for checkpoint in checkpoints:
            # Verify signature
            sig_valid = verify_checkpoint_signature(checkpoint)
            results["checkpoints_valid"].append(sig_valid)
            
            if not sig_valid:
                results["issues"].append(
                    f"Checkpoint {checkpoint.id} signature invalid"
                )
            
            # Verify Merkle tree
            merkle_valid, issue = verify_checkpoint_merkle_tree(checkpoint)
            results["merkle_valid"].append(merkle_valid)
            
            if not merkle_valid:
                results["issues"].append(
                    f"Checkpoint {checkpoint.id} Merkle tree invalid: {issue}"
                )
    finally:
        db.close()
    
    # Overall result
    results["overall_valid"] = (
        chain_valid and
        all(results["checkpoints_valid"]) and
        all(results["merkle_valid"])
    )
    
    return results


if __name__ == "__main__":
    # Test verification
    print("Log Verification Module Test")
    print("=" * 60)
    
    # Verify hash chain
    print("\n1. Verifying hash chain...")
    chain_valid, issues = verify_log_chain()
    
    if chain_valid:
        print("✓ Hash chain is valid")
    else:
        print("✗ Hash chain has issues:")
        for issue in issues:
            print(f"   {issue}")
    
    # Full verification
    print("\n2. Running full verification...")
    results = full_verification()
    
    print(f"\nResults:")
    print(f"   Chain valid: {results['chain_valid']}")
    print(f"   Checkpoints signed: {len(results['checkpoints_valid'])}")
    print(f"   Merkle trees valid: {sum(results['merkle_valid'])}/{len(results['merkle_valid'])}")
    print(f"   Overall valid: {results['overall_valid']}")
    
    if results["issues"]:
        print(f"\nIssues found: {len(results['issues'])}")
        for issue in results["issues"]:
            print(f"   - {issue}")
    
    print("\n" + "=" * 60)
    print("Verification module test complete!")

