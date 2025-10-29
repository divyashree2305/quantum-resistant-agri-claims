"""
FastAPI main application for Post-Quantum Secure Insurance Claim System.

Implements secure channel setup, claim submission with AI fraud detection,
checkpoint generation, and audit verification endpoints.
"""

import base64
import uuid
import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import crypto
from api.session_manager import create_session, validate_session, get_session
from ai.ai_score import score_claim
import append_log
import checkpoint
from audit_verify import verify_checkpoint as verify_checkpoint_func, prove_inclusion as prove_inclusion_func, verify_ai_score as verify_ai_score_func

app = FastAPI(
    title="Insurance Claim System API",
    description="Post-Quantum Secure Insurance Claim Management",
    version="0.5.0"
)

# Configure CORS
# Get allowed origins from environment or use defaults
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class HandshakeRequest(BaseModel):
    """Request model for Kyber handshake"""
    client_public_key: str = Field(..., description="Client's Kyber public key (base64 encoded)")


class HandshakeResponse(BaseModel):
    """Response model for Kyber handshake"""
    server_public_key: str
    ciphertext: str
    session_token: str


class ClaimSubmitRequest(BaseModel):
    """Request model for claim submission"""
    claim_data: Dict[str, Any] = Field(..., description="Claim data dictionary")


class ClaimSubmitResponse(BaseModel):
    """Response model for claim submission"""
    success: bool
    log_entry_id: int
    fraud_score: float
    model_version: str


class CheckpointResponse(BaseModel):
    """Response model for checkpoint generation"""
    success: bool
    checkpoint_id: int
    merkle_root: str
    entries_range: str
    epoch_id: str


# Session validation dependency
async def get_valid_session(
    session_token: Optional[str] = Header(None, alias="X-Session-Token")
) -> str:
    """
    FastAPI dependency to validate session token.
    
    Args:
        session_token: Session token from header
        
    Returns:
        Validated session token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Session token required. Use X-Session-Token header."
        )
    
    if not validate_session(session_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token. Please perform handshake."
        )
    
    return session_token


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "insurance-claim-system",
        "version": "0.5.0"
    })


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({
        "message": "Post-Quantum Secure Insurance Claim System",
        "phase": "5 & 6 - API Integration & Audit",
        "status": "operational"
    })


@app.post("/handshake", response_model=HandshakeResponse)
async def handshake(request: HandshakeRequest):
    """
    Establish secure channel using Kyber KEM (ML-KEM-1024).
    
    Process:
    1. Accept client's Kyber public key
    2. Server generates its own Kyber keypair
    3. Server encapsulates shared secret using client's public key
    4. Create session and return server public key, ciphertext, and session token
    
    Returns:
        Server public key, ciphertext, and session token (all base64 encoded)
    """
    try:
        # Decode client's public key
        try:
            client_public_key = base64.b64decode(request.client_public_key)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 encoding for client_public_key: {str(e)}"
            )
        
        # Validate key length (ML-KEM-1024 public key should be 1568 bytes)
        if len(client_public_key) != 1568:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid public key length: expected 1568 bytes (ML-KEM-1024), got {len(client_public_key)} bytes"
            )
        
        # Generate server's Kyber keypair
        try:
            server_public_key, server_private_key = crypto.generate_kyber_keypair()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate server keypair: {str(e)}"
            )
        
        # Encapsulate shared secret using client's public key
        try:
            shared_secret, ciphertext = crypto.kyber_encapsulate(client_public_key)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to encapsulate shared secret: {str(e)}"
            )
        
        # Create session
        try:
            session_token = create_session(
                client_public_key=client_public_key,
                server_private_key=server_private_key,
                shared_secret=shared_secret,
                ciphertext=ciphertext
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )
        
        # Encode for response
        return HandshakeResponse(
            server_public_key=base64.b64encode(server_public_key).decode('utf-8'),
            ciphertext=base64.b64encode(ciphertext).decode('utf-8'),
            session_token=session_token
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Handshake failed with unexpected error: {str(e)}\n{error_details}"
        )


@app.post("/claim/submit", response_model=ClaimSubmitResponse)
async def submit_claim(
    request: ClaimSubmitRequest,
    session_token: str = Depends(get_valid_session)
):
    """
    Submit insurance claim with AI fraud detection.
    
    Process:
    1. Score claim using AI fraud detection model
    2. Bundle original claim + AI score into event data
    3. Log to tamper-evident append-only log
    4. Return success with log entry ID and fraud score
    
    Requires:
        Valid session token in X-Session-Token header
    """
    try:
        # Generate claim ID if not provided
        claim_id = request.claim_data.get("claim_id")
        if not claim_id:
            claim_id = str(uuid.uuid4())
        
        # Score claim using AI model (Phase 4)
        score_result = score_claim(request.claim_data)
        
        # Bundle original claim + AI score into event data
        event_data = {
            "original_claim": request.claim_data,
            "fraud_score": score_result["score"],
            "model_version": score_result["model_version"],
            "feature_hash": score_result["feature_hash"],
            "features_used": score_result["features_used"]
        }
        
        # Log to tamper-evident log (Phase 3)
        log_entry = append_log.add_log_event(
            claim_id=claim_id,
            event_type="claim_submitted",
            event_data=event_data
        )
        
        return ClaimSubmitResponse(
            success=True,
            log_entry_id=log_entry.id,
            fraud_score=score_result["score"],
            model_version=score_result["model_version"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claim submission failed: {str(e)}"
        )


@app.post("/admin/generate-checkpoint", response_model=CheckpointResponse)
async def generate_checkpoint_endpoint(
    admin_key: Optional[str] = Query(None, description="Admin API key (optional for demo)")
):
    """
    Generate Merkle tree checkpoint (admin endpoint).
    
    Process:
    1. Find log entries since last checkpoint
    2. Build Merkle tree
    3. Sign Merkle root with current epoch Dilithium key
    4. Save checkpoint to database
    
    Optional:
        Admin API key validation (via ADMIN_API_KEY env var)
    """
    import os
    
    # Check admin key if configured
    expected_key = os.getenv("ADMIN_API_KEY")
    if expected_key and admin_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin API key"
        )
    
    try:
        # Generate checkpoint (Phase 3)
        checkpoint_obj = checkpoint.generate_checkpoint()
        
        return CheckpointResponse(
            success=True,
            checkpoint_id=checkpoint_obj.id,
            merkle_root=checkpoint_obj.merkle_root.hex(),
            entries_range=checkpoint_obj.entries_range,
            epoch_id=checkpoint_obj.signer_id or "unknown"
        )
    
    except ValueError as e:
        # No new entries to checkpoint
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Checkpoint generation failed: {str(e)}"
        )


@app.get("/audit/verify-checkpoint/{checkpoint_id}")
async def verify_checkpoint_endpoint(checkpoint_id: int):
    """
    Verify checkpoint signature and integrity.
    
    Returns:
        Verification result with validity status
    """
    try:
        result = verify_checkpoint_func(checkpoint_id)
        return JSONResponse(result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


@app.get("/audit/prove-inclusion/{log_entry_id}")
async def prove_inclusion_endpoint(log_entry_id: int):
    """
    Generate Merkle inclusion proof for a log entry.
    
    Returns:
        Merkle proof path and checkpoint information
    """
    try:
        result = prove_inclusion_func(log_entry_id)
        return JSONResponse(result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inclusion proof generation failed: {str(e)}"
        )


@app.get("/audit/verify-ai-score/{log_entry_id}")
async def verify_ai_score_endpoint(log_entry_id: int):
    """
    Verify AI score lineage and feature hash integrity.
    
    Returns:
        Verification result showing feature hash match and model version
    """
    try:
        result = verify_ai_score_func(log_entry_id)
        return JSONResponse(result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI score verification failed: {str(e)}"
        )

