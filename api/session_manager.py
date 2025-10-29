"""
Session Manager for Kyber KEM Handshake

Manages session tokens and shared secrets from Kyber key exchange.
For demo purposes, uses in-memory storage.
"""

import uuid
import base64
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

# In-memory session storage
_sessions: Dict[str, Dict] = {}

# Session expiration time (in seconds) - default 1 hour
SESSION_EXPIRY_SECONDS = 3600


def create_session(
    client_public_key: bytes,
    server_private_key: bytes,
    shared_secret: bytes,
    ciphertext: bytes
) -> str:
    """
    Create a new session from Kyber handshake.
    
    Args:
        client_public_key: Client's Kyber public key
        server_private_key: Server's Kyber private key
        shared_secret: Encapsulated shared secret
        ciphertext: Kyber ciphertext
        
    Returns:
        Session token (UUID string)
    """
    # Generate unique session token
    session_token = str(uuid.uuid4())
    
    # Store session data
    _sessions[session_token] = {
        "client_public_key": client_public_key,
        "server_private_key": server_private_key,
        "shared_secret": shared_secret,
        "ciphertext": ciphertext,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(seconds=SESSION_EXPIRY_SECONDS)
    }
    
    return session_token


def get_session(session_token: str) -> Optional[Dict]:
    """
    Retrieve session by token.
    
    Args:
        session_token: Session token UUID
        
    Returns:
        Session dictionary if valid, None otherwise
    """
    if session_token not in _sessions:
        return None
    
    session = _sessions[session_token]
    
    # Check expiration
    if datetime.utcnow() > session["expires_at"]:
        # Remove expired session
        del _sessions[session_token]
        return None
    
    return session


def validate_session(session_token: str) -> bool:
    """
    Check if session token is valid and not expired.
    
    Args:
        session_token: Session token UUID
        
    Returns:
        True if valid, False otherwise
    """
    session = get_session(session_token)
    return session is not None


def delete_session(session_token: str) -> bool:
    """
    Delete a session.
    
    Args:
        session_token: Session token UUID
        
    Returns:
        True if deleted, False if not found
    """
    if session_token in _sessions:
        del _sessions[session_token]
        return True
    return False


def cleanup_expired_sessions():
    """Remove all expired sessions from storage."""
    current_time = datetime.utcnow()
    expired_tokens = [
        token for token, session in _sessions.items()
        if current_time > session["expires_at"]
    ]
    
    for token in expired_tokens:
        del _sessions[token]
    
    return len(expired_tokens)


def get_session_count() -> int:
    """Get total number of active sessions."""
    cleanup_expired_sessions()
    return len(_sessions)


