-- PostgreSQL Database Initialization Script
-- For Post-Quantum Secure Insurance Claim System

-- Set encoding
SET client_encoding = 'UTF8';

-- Create extension for better performance (optional)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text similarity searches
-- CREATE EXTENSION IF NOT EXISTS btree_gin;  -- For GIN indexes on foreign keys

-- Note: Tables are created by SQLAlchemy models
-- This script is for any additional database setup, indexes, or views

-- Create indexes for optimized queries
-- (Additional indexes beyond those defined in SQLAlchemy models)

-- Index for searching log entries by claim_id and date range
-- CREATE INDEX IF NOT EXISTS idx_log_claim_date_range 
-- ON log_entries(claim_id, timestamp_local DESC);

-- Index for checkpoint verification lookups
-- CREATE INDEX IF NOT EXISTS idx_checkpoint_hash 
-- ON checkpoints(prev_checkpoint_hash);

-- Function to get current active epoch (optional helper)
CREATE OR REPLACE FUNCTION get_active_epoch()
RETURNS TABLE (epoch_id VARCHAR, public_key BYTEA, created_at TIMESTAMP)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT ek.epoch_id, ek.public_key_ml_dsa, ek.created_at
    FROM epoch_keys ek
    WHERE ek.is_retired = FALSE
    ORDER BY ek.created_at DESC
    LIMIT 1;
END;
$$;

-- Function to get log entries for a specific claim (optional helper)
CREATE OR REPLACE FUNCTION get_claim_logs(p_claim_id VARCHAR)
RETURNS TABLE (
    id INTEGER,
    event_type VARCHAR,
    timestamp_local TIMESTAMP,
    prev_hash BYTEA
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT le.id, le.event_type, le.timestamp_local, le.prev_hash
    FROM log_entries le
    WHERE le.claim_id = p_claim_id
    ORDER BY le.timestamp_local ASC;
END;
$$;

-- View for checkpoint chain verification (optional)
CREATE OR REPLACE VIEW checkpoint_chain AS
SELECT 
    c.id,
    c.merkle_root,
    c.entries_range,
    c.prev_checkpoint_hash,
    c.signer_id,
    c.created_at,
    LAG(c.id) OVER (ORDER BY c.created_at) as prev_checkpoint_id
FROM checkpoints c
ORDER BY c.created_at ASC;

-- Grant permissions (adjust as needed for your security model)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO insurance_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO insurance_app;

COMMENT ON FUNCTION get_active_epoch() IS 'Get the currently active epoch for signing operations';
COMMENT ON FUNCTION get_claim_logs(VARCHAR) IS 'Get all log entries for a specific claim in chronological order';
COMMENT ON VIEW checkpoint_chain IS 'View showing the checkpoint chain with linked previous checkpoints';

