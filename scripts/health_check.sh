#!/bin/bash
# Health check script for the insurance claim system

# Check if the FastAPI health endpoint is responding
curl -f http://localhost:8000/health || exit 1

