# How to Clear the Database or Merkle Tree

This guide shows you different methods to clear the database or Merkle tree data.

## ⚠️ WARNING
All these operations will delete data. Make sure you have backups if needed!

---

## Method 1: Complete Database Reset (Drop All Tables)

This completely removes all tables and data. You'll need to run `init_db()` afterwards to recreate the tables.

### Using Python (Local)
```bash
python -c "from models.database import drop_db, init_db; drop_db(); init_db()"
```

### Using Docker
```bash
# Drop all tables
docker-compose exec insurance-backend python -c "from models.database import drop_db; drop_db()"

# Recreate tables (optional)
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"
```

### Using Python Script
Create a file `clear_db.py`:
```python
from models.database import drop_db, init_db

print("Dropping all database tables...")
drop_db()

print("Recreating database tables...")
init_db()

print("Done!")
```

Run it:
```bash
python clear_db.py
# Or with Docker:
docker-compose exec insurance-backend python clear_db.py
```

---

## Method 2: Clear Specific Tables (Keep Structure)

This clears the data but keeps the table structure intact.

### Clear All Log Entries and Checkpoints (Python)

Create a file `clear_data.py`:
```python
from models.database import get_session, LogEntry, Checkpoint, EpochKeys

db = get_session()
try:
    # Clear log entries
    deleted_logs = db.query(LogEntry).delete()
    print(f"Deleted {deleted_logs} log entries")
    
    # Clear checkpoints
    deleted_checkpoints = db.query(Checkpoint).delete()
    print(f"Deleted {deleted_checkpoints} checkpoints")
    
    # Optionally clear epoch keys (be careful - this may break existing signatures)
    # deleted_epochs = db.query(EpochKeys).delete()
    # print(f"Deleted {deleted_epochs} epoch keys")
    
    db.commit()
    print("✓ Database cleared successfully!")
except Exception as e:
    db.rollback()
    print(f"✗ Error: {e}")
finally:
    db.close()
```

Run it:
```bash
python clear_data.py
# Or with Docker:
docker-compose exec insurance-backend python clear_data.py
```

### Clear Only Log Entries (keeps checkpoints)
```python
from models.database import get_session, LogEntry

db = get_session()
try:
    deleted = db.query(LogEntry).delete()
    db.commit()
    print(f"Deleted {deleted} log entries")
finally:
    db.close()
```

### Clear Only Checkpoints (keeps log entries)
```python
from models.database import get_session, Checkpoint

db = get_session()
try:
    deleted = db.query(Checkpoint).delete()
    db.commit()
    print(f"Deleted {deleted} checkpoints")
finally:
    db.close()
```

---

## Method 3: Using SQL Directly

Connect to PostgreSQL and run SQL commands:

### Using Docker PostgreSQL Client
```bash
docker-compose exec postgres psql -U insurance -d insurance_claims
```

### Clear All Data (SQL)
```sql
-- Clear log entries
DELETE FROM log_entries;

-- Clear checkpoints
DELETE FROM checkpoints;

-- Clear epoch keys (optional - may break verification)
DELETE FROM epoch_keys;

-- Reset sequences (so IDs start from 1 again)
ALTER SEQUENCE log_entries_id_seq RESTART WITH 1;
ALTER SEQUENCE checkpoints_id_seq RESTART WITH 1;
```

### Truncate Tables (Faster than DELETE)
```sql
-- Truncate all tables (cascades to related data)
TRUNCATE TABLE log_entries, checkpoints CASCADE;

-- Reset sequences
ALTER SEQUENCE log_entries_id_seq RESTART WITH 1;
ALTER SEQUENCE checkpoints_id_seq RESTART WITH 1;
```

### One-liner from Command Line
```bash
docker-compose exec postgres psql -U insurance -d insurance_claims -c "TRUNCATE TABLE log_entries, checkpoints CASCADE; ALTER SEQUENCE log_entries_id_seq RESTART WITH 1; ALTER SEQUENCE checkpoints_id_seq RESTART WITH 1;"
```

---

## Method 4: Clear Merkle Tree Only

The Merkle tree is computed from log entries, so clearing log entries will effectively clear the Merkle tree. However, if you want to clear checkpoints (which contain Merkle roots) but keep log entries:

```python
from models.database import get_session, Checkpoint

db = get_session()
try:
    deleted = db.query(Checkpoint).delete()
    db.commit()
    print(f"Deleted {deleted} checkpoints (Merkle roots)")
    print("Note: Log entries still exist. Generate new checkpoint to rebuild Merkle tree.")
finally:
    db.close()
```

Or using SQL:
```sql
DELETE FROM checkpoints;
ALTER SEQUENCE checkpoints_id_seq RESTART WITH 1;
```

---

## Method 5: Clear via API (If Admin Endpoint Exists)

Currently, there's no API endpoint to clear the database (for security reasons). You would need to add one:

```python
@app.post("/admin/clear-database")
async def clear_database_endpoint(
    admin_key: Optional[str] = Query(None),
    confirm: bool = Query(False)
):
    """Admin endpoint to clear all data"""
    import os
    expected_key = os.getenv("ADMIN_API_KEY")
    if expected_key and admin_key != expected_key:
        raise HTTPException(403, "Invalid admin API key")
    
    if not confirm:
        raise HTTPException(400, "Must set confirm=true")
    
    from models.database import get_session, LogEntry, Checkpoint
    db = get_session()
    try:
        db.query(LogEntry).delete()
        db.query(Checkpoint).delete()
        db.commit()
        return {"success": True, "message": "Database cleared"}
    finally:
        db.close()
```

---

## Recommended: Complete Reset Script

Here's a complete script that safely clears everything:

**`scripts/clear_database.py`**:
```python
#!/usr/bin/env python3
"""
Clear Database Script
Clears all log entries and checkpoints, optionally resets epoch keys.
"""

import sys
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
        db.execute("ALTER SEQUENCE log_entries_id_seq RESTART WITH 1")
        db.execute("ALTER SEQUENCE checkpoints_id_seq RESTART WITH 1")
        db.commit()
        print("✓ Sequences reset")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    clear_epochs = "--clear-epochs" in sys.argv
    clear_database(clear_epoch_keys=clear_epochs)
```

Usage:
```bash
# Clear log entries and checkpoints (keep epoch keys)
python scripts/clear_database.py

# Clear everything including epoch keys
python scripts/clear_database.py --clear-epochs

# With Docker
docker-compose exec insurance-backend python scripts/clear_database.py
```

---

## Quick Reference

| What to Clear | Method | Command |
|--------------|--------|---------|
| **Everything** | Drop & Recreate | `drop_db(); init_db()` |
| **All Data** | Python | `DELETE FROM log_entries, checkpoints` |
| **All Data** | SQL | `TRUNCATE TABLE log_entries, checkpoints CASCADE` |
| **Log Entries Only** | Python | `db.query(LogEntry).delete()` |
| **Checkpoints Only** | Python | `db.query(Checkpoint).delete()` |
| **Merkle Tree** | Clear Log Entries | Same as clearing log entries |

---

## Notes

- **Epoch Keys**: Be careful clearing epoch keys. If you clear them, existing checkpoint signatures will become unverifiable because the public keys are gone.
- **Sequences**: After clearing, reset sequences so IDs start from 1 again.
- **Merkle Tree**: The Merkle tree is computed dynamically from log entries. Clearing log entries effectively clears the Merkle tree.
- **Checkpoints**: Checkpoints contain signed Merkle roots. If you clear checkpoints but keep log entries, you can generate new checkpoints.

