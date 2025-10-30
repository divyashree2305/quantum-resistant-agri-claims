#!/usr/bin/env python3
"""
Clear Database Script
Clears all log entries and checkpoints, optionally resets epoch keys.
"""

import sys
from sqlalchemy import text
from models.database import get_session, LogEntry, Checkpoint, EpochKeys

def clear_database(clear_epoch_keys=False):
    """Clear database tables"""
    db = get_session()
    try:
        # Clear log entries
        deleted_logs = db.query(LogEntry).delete()
        print(f"✓ Deleted {deleted_logs} log entries")
        
        # Clear checkpoints
        deleted_checkpoints = db.query(Checkpoint).delete()
        print(f"✓ Deleted {deleted_checkpoints} checkpoints")
        
        # Optionally clear epoch keys
        if clear_epoch_keys:
            deleted_epochs = db.query(EpochKeys).delete()
            print(f"✓ Deleted {deleted_epochs} epoch keys")
        else:
            print("⚠ Keeping epoch keys (existing signatures may become invalid)")
        
        db.commit()
        print("\n✓ Database cleared successfully!")
        
        # Reset sequences
        db.execute(text("ALTER SEQUENCE log_entries_id_seq RESTART WITH 1"))
        db.execute(text("ALTER SEQUENCE checkpoints_id_seq RESTART WITH 1"))
        db.commit()
        print("✓ Sequences reset")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    clear_epochs = "--clear-epochs" in sys.argv
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage:")
        print("  python scripts/clear_database.py           # Clear log entries and checkpoints")
        print("  python scripts/clear_database.py --clear-epochs  # Clear everything including epoch keys")
        sys.exit(0)
    
    clear_database(clear_epoch_keys=clear_epochs)

