"""
Database Models for Post-Quantum Secure Insurance Claim System

Defines three core tables for tamper-evident logging:
1. LogEntry - Append-only claim event log with hash chain linkage
2. Checkpoint - Merkle root anchoring points with Dilithium signatures
3. EpochKeys - Rotating Dilithium public keys for epoch-based signing
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, 
    Text, Index, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import BYTEA
from typing import Optional
import os

Base = declarative_base()


class LogEntry(Base):
    """
    Append-only log table for claim events.
    
    Maintains a hash chain for tamper detection:
    - Each entry hashes the previous entry's hash
    - Creates tamper-evident audit trail
    """
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # e.g., "submit", "review", "approve", "reject"
    timestamp_local = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload_hash = Column(BYTEA, nullable=False)  # SHA3-256 of event data
    prev_hash = Column(BYTEA, nullable=False)  # Hash chain linkage
    actor_sig = Column(BYTEA, nullable=True)  # Optional Dilithium signature from actor
    epoch_id = Column(String(50), ForeignKey('epoch_keys.epoch_id'), nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_claim_timestamp', 'claim_id', 'timestamp_local'),
        Index('idx_event_type', 'event_type'),
    )
    
    # Relationships
    epoch = relationship("EpochKeys", back_populates="log_entries")
    
    def __repr__(self):
        return f"<LogEntry(claim_id={self.claim_id}, event_type={self.event_type}, timestamp={self.timestamp_local})>"


class Checkpoint(Base):
    """
    Merkle root checkpoint table.
    
    Creates periodic snapshots of the log state:
    - Merkle root of all log entries in range
    - Signed with Dilithium for authenticity
    - Forms checkpoint chain for integrity
    """
    __tablename__ = "checkpoints"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    merkle_root = Column(BYTEA, nullable=False)  # Root of Merkle tree of log entries
    entries_range = Column(String(50), nullable=False)  # e.g., "1-100"
    prev_checkpoint_hash = Column(BYTEA, nullable=False)  # Links to previous checkpoint
    signer_id = Column(String(50), nullable=False)  # Epoch identifier
    signer_ml_dsa_sig = Column(BYTEA, nullable=False)  # Dilithium signature of merkle_root
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_checkpoint_created', 'created_at'),
        Index('idx_checkpoint_signer', 'signer_id'),
    )
    
    def __repr__(self):
        return f"<Checkpoint(id={self.id}, signer={self.signer_id}, range={self.entries_range})>"


class EpochKeys(Base):
    """
    Epoch-based public key rotation table.
    
    Stores Dilithium public keys for different time periods:
    - Enables key rotation for long-term security
    - Links log entries to specific epochs
    - Supports key retirement workflow
    """
    __tablename__ = "epoch_keys"
    
    epoch_id = Column(String(50), primary_key=True)  # e.g., "2025-10-28"
    public_key_ml_dsa = Column(BYTEA, nullable=False)  # Dilithium public key
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_epoch_active', 'is_retired'),
    )
    
    # Relationships
    log_entries = relationship("LogEntry", back_populates="epoch")
    
    def __repr__(self):
        return f"<EpochKeys(epoch_id={self.epoch_id}, retired={self.is_retired})>"


# Database connection management
_db_engine = None
_SessionLocal = None


def get_db_engine(db_url: Optional[str] = None):
    """
    Get or create database engine.
    
    Args:
        db_url: Database connection URL. Defaults to environment variable.
        
    Returns:
        SQLAlchemy engine
    """
    global _db_engine
    
    if _db_engine is None:
        if db_url is None:
            db_url = os.environ.get(
                "DATABASE_URL",
                "postgresql://insurance:insurance_password@localhost:5432/insurance_claims"
            )
        
        _db_engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
    
    return _db_engine


def get_session():
    """
    Get database session.
    
    Returns:
        SQLAlchemy session
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_db_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    
    return _SessionLocal()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    engine = get_db_engine()
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def drop_db():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    engine = get_db_engine()
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully!")


if __name__ == "__main__":
    # Initialize database
    print("Initializing database...")
    init_db()
    print("Done!")

