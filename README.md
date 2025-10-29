# Post-Quantum Secure Insurance Claim System

A secure, tamper-evident insurance claim management system using post-quantum cryptographic primitives (Kyber for key exchange, Dilithium for signatures) and AI-driven fraud detection.

**Repository:** [https://github.com/divyashree2305/quantum-resistant-agri-claims](https://github.com/divyashree2305/quantum-resistant-agri-claims)

## Overview

This system protects farmers' insurance claim data against both classical and quantum threats using:

- **Lattice-based Cryptography**: CRYSTALS Kyber (ML-KEM-1024) and CRYSTALS Dilithium (ML-DSA-3)
- **Tamper-Evident Logging**: Hash chains and Merkle tree checkpoints without blockchain overhead
- **AI Fraud Detection**: Anomaly detection models for suspicious claim patterns

## Architecture

### Phase 1 Foundation

- Post-quantum cryptographic primitives (SHA3, Dilithium, Kyber)
- PostgreSQL database with tamper-evident logging
- Docker containerized deployment

### Key Components

1. **crypto.py**: Unified cryptographic wrapper for all post-quantum operations
2. **models/database.py**: SQLAlchemy models for LogEntry, Checkpoint, and EpochKeys
3. **Docker**: Full containerized environment with PostgreSQL and Redis

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/divyashree2305/quantum-resistant-agri-claims.git
cd quantum-resistant-agri-claims
```

2. Build and start the services:
```bash
docker-compose up -d --build
```

3. Initialize the database:
```bash
docker-compose exec insurance-backend python -c "from models.database import init_db; init_db()"
```

4. Run tests:
```bash
docker-compose exec insurance-backend python tests/test_crypto.py
# Or directly
python tests/test_crypto.py
```

### Verify Setup

- Backend API: http://localhost:8000
- PgAdmin (development): http://localhost:8080 (admin@insurance.local / admin_password)
- Redis Commander (development): http://localhost:8081

## Project Structure

```
.
├── crypto.py                 # Post-quantum cryptographic wrapper
├── models/                   # Database models
│   ├── __init__.py
│   └── database.py           # LogEntry, Checkpoint, EpochKeys tables
├── scripts/
│   ├── init_db.sql          # PostgreSQL initialization
│   └── health_check.sh      # Health check script
├── tests/
│   ├── __init__.py
│   └── test_crypto.py       # Crypto operation tests
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Features

### Tamper-Evident Logging

- Append-only log entries with hash chain linkage
- Merkle root checkpoints signed with Dilithium
- Epoch-based key rotation for long-term security

### Post-Quantum Security

- **SHA3-256**: Quantum-resistant hashing
- **Dilithium-3**: Digital signatures (~4KB signatures)
- **Kyber-1024**: Key encapsulation mechanism

### Performance

- Lightweight tamper-evident mechanism (no blockchain)
- Fast cryptographic operations
- Scalable PostgreSQL backend

## Development

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test file
python tests/test_crypto.py

# With Docker
docker-compose exec insurance-backend python tests/test_crypto.py
```

### Database Operations

```bash
# Initialize database
python -c "from models.database import init_db; init_db()"

# Drop database (WARNING: Deletes all data)
python -c "from models.database import drop_db; drop_db()"

# Access PostgreSQL directly
docker-compose exec postgres psql -U insurance -d insurance_claims
```

## Security Notes

- This is a research/educational project
- Cryptographic libraries use mock implementations when unavailable
- For production use, ensure proper key management and security practices

## License

[Specify License]

