"""
Append-Only Log Module (Phase 3)

Implements tamper-evident logging with cryptographic hash chains.
Each log entry is cryptographically linked to the previous entry,
making any modification detectable.
"""

import json
from datetime import datetime
from typing import Optional
from models.database import LogEntry, get_session
from models.database import init_db
import crypto


def get_last_log_entry() -> Optional[LogEntry]:
    """Get the most recent log entry for chain linkage"""
    db = get_session()
    try:
        last_entry = db.query(LogEntry).order_by(LogEntry.id.desc()).first()
        return last_entry
    finally:
        db.close()


def compute_payload_hash(event_data: dict) -> bytes:
    """
    Hash event data payload using SHA3-256.
    
    Args:
        event_data: Event payload as dictionary
        
    Returns:
        SHA3-256 hash as bytes (32 bytes)
    """
    # Convert dictionary to JSON string deterministically
    # Use sort_keys=True for consistent ordering
    json_str = json.dumps(event_data, sort_keys=True)
    return crypto.hash_data(json_str.encode('utf-8'))


def compute_chain_hash(prev_hash: bytes, payload_hash: bytes, timestamp: datetime) -> bytes:
    """
    Compute hash chain link: h_i = H(h_{i-1} || payload_hash || timestamp)
    
    Args:
        prev_hash: Hash of previous log entry
        payload_hash: Hash of current event data
        timestamp: Timestamp of the event
        
    Returns:
        Chain hash as bytes
    """
    # Convert timestamp to bytes (ISO format)
    timestamp_bytes = timestamp.isoformat().encode('utf-8')
    
    # Combine: prev_hash || payload_hash || timestamp
    combined = prev_hash + payload_hash + timestamp_bytes
    
    # Hash the combination
    return crypto.hash_data(combined)


def add_log_event(
    claim_id: str,
    event_type: str,
    event_data: dict,
    actor_sig: Optional[bytes] = None
) -> LogEntry:
    """
    Add a new event to the tamper-evident log.
    
    Process:
    1. Get prev_hash from most recent LogEntry
    2. Hash event_data to get payload_hash (SHA3-256)
    3. Create chain hash: h_i = H(h_{i-1} || payload_hash || timestamp)
    4. Save new LogEntry with computed hash
    5. Return LogEntry object
    
    Args:
        claim_id: Insurance claim identifier
        event_type: Type of event (e.g., "submit", "review", "approve")
        event_data: Event payload as dictionary
        actor_sig: Optional Dilithium signature from actor
        
    Returns:
        Created LogEntry database object
    """
    db = get_session()
    
    try:
        # Get the previous log entry for chain linkage
        last_entry = get_last_log_entry()
        
        if last_entry:
            prev_hash = last_entry.prev_hash
        else:
            # Genesis hash for first entry
            prev_hash = crypto.hash_data(b"GENESIS")
        
        # Compute payload hash
        payload_hash = compute_payload_hash(event_data)
        
        # Get current timestamp
        timestamp = datetime.utcnow()
        
        # Compute chain hash
        chain_hash = compute_chain_hash(prev_hash, payload_hash, timestamp)
        
        # Create new log entry
        log_entry = LogEntry(
            claim_id=claim_id,
            event_type=event_type,
            timestamp_local=timestamp,
            payload_hash=payload_hash,
            prev_hash=chain_hash,
            actor_sig=actor_sig,
            epoch_id=None  # Can be set if using epoch-based signing
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return log_entry
    
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to add log event: {e}")
    
    finally:
        db.close()


def get_log_entries_for_claim(claim_id: str) -> list:
    """
    Retrieve all log entries for a specific claim.
    
    Args:
        claim_id: Insurance claim identifier
        
    Returns:
        List of LogEntry objects for the claim
    """
    db = get_session()
    
    try:
        entries = db.query(LogEntry)\
            .filter_by(claim_id=claim_id)\
            .order_by(LogEntry.timestamp_local.asc())\
            .all()
        return entries
    finally:
        db.close()


def get_log_entry_by_id(entry_id: int) -> Optional[LogEntry]:
    """
    Retrieve a log entry by its ID.
    
    Args:
        entry_id: Log entry ID
        
    Returns:
        LogEntry object or None if not found
    """
    db = get_session()
    
    try:
        return db.query(LogEntry).filter_by(id=entry_id).first()
    finally:
        db.close()


if __name__ == "__main__":
    # Test append-only log functionality
    print("Append-Only Log Module Test")
    print("=" * 60)
    
    # Initialize database if needed
    try:
        init_db()
        print("✓ Database initialized")
    except:
        print("Note: Database already initialized or not connected")
    
    # Test 1: Add first log entry (genesis)
    print("\n1. Adding first log entry...")
    entry1 = add_log_event(
        claim_id="CLAIM-001",
        event_type="submit",
        event_data={
            "farmer_name": "John Doe",
            "crop_type": "Corn",
            "damage_amount": 5000,
            "submission_date": "2025-10-15"
        }
    )
    print(f"   Entry ID: {entry1.id}")
    print(f"   Claim ID: {entry1.claim_id}")
    print(f"   Event Type: {entry1.event_type}")
    print(f"   Chain Hash (hex): {entry1.prev_hash.hex()[:16]}...")
    
    # Test 2: Add second log entry (chain to first)
    print("\n2. Adding second log entry (chained)...")
    entry2 = add_log_event(
        claim_id="CLAIM-001",
        event_type="review",
        event_data={
            "reviewer": "Alice Smith",
            "status": "under_review",
            "notes": "Documentation complete"
        }
    )
    print(f"   Entry ID: {entry2.id}")
    print(f"   Chain Hash (hex): {entry2.prev_hash.hex()[:16]}...")
    
    # Test 3: Retrieve entries for claim
    print("\n3. Retrieving entries for CLAIM-001...")
    entries = get_log_entries_for_claim("CLAIM-001")
    print(f"   Found {len(entries)} entries")
    for i, entry in enumerate(entries, 1):
        print(f"   {i}. {entry.event_type} at {entry.timestamp_local}")
    
    print("\n" + "=" * 60)
    print("Append-only log test complete!")

