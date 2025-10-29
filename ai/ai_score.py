"""
AI Fraud Detection Scoring Module

Provides fraud detection scoring using pre-trained machine learning models.
Implements singleton pattern for efficient model loading and flexible feature extraction.
"""

import json
import pickle
from datetime import datetime
from typing import Dict, Tuple
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import crypto
from ai.config import MODEL_CONFIG, EXPECTED_FEATURES


class ModelLoader:
    """Singleton class for loading and caching fraud detection model"""
    
    _instance = None
    _model = None
    _model_version = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Load model once at startup"""
        if self._model is None:
            model_path = MODEL_CONFIG["model_path"]
            try:
                with open(model_path, "rb") as f:
                    self._model = pickle.load(f)
                self._model_version = MODEL_CONFIG["model_version"]
            except FileNotFoundError:
                raise RuntimeError(
                    f"Model file not found: {model_path}. "
                    "Please ensure fraud_model.pkl exists in ai/ directory."
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load model: {e}")
        return self._model


def extract_features(claim_data: dict) -> Tuple[np.ndarray, dict]:
    """
    Extract features from claim_data dict to match model training format.
    
    Model was trained with 3 features: claim_am, time_of_c, location_r
    We map user-friendly names to the exact feature names used in training.
    
    Args:
        claim_data: Dictionary with claim information
        Expected keys: "claim_amount" or "claim_am", "time_of_day" or "time_of_c", 
                       "location_risk" or "location_r"
        
    Returns:
        (feature_vector, feature_dict) tuple
        - feature_vector: numpy array ready for model (3 features)
        - feature_dict: dict of extracted features for hashing
    """
    from ai.config import FEATURE_MAPPING, EXPECTED_FEATURES
    
    features = {}
    
    # Map user-friendly names to training feature names
    # Support both the original training names and user-friendly names
    features["claim_am"] = claim_data.get("claim_am") or claim_data.get("claim_amount", 0.0)
    features["time_of_c"] = claim_data.get("time_of_c") or claim_data.get("time_of_day", 12)  # noon default
    features["location_r"] = claim_data.get("location_r") or claim_data.get("location_risk", 0.5)  # medium risk
    
    # Extract hour from timestamp if available and no explicit time provided
    if "timestamp" in claim_data and "time_of_c" not in claim_data and "time_of_day" not in claim_data:
        try:
            dt = datetime.fromisoformat(claim_data["timestamp"])
            features["time_of_c"] = dt.hour
        except (ValueError, AttributeError):
            pass
    
    # Build feature vector in exact order expected by the model
    # Model expects: [claim_am, time_of_c, location_r]
    feature_vector = np.array([
        features.get(f, 0.0) for f in EXPECTED_FEATURES
    ], dtype=np.float64)
    
    # Also store in both formats for compatibility
    feature_dict = {
        "claim_am": features["claim_am"],
        "time_of_c": features["time_of_c"],
        "location_r": features["location_r"],
        # Also include mapped names for backward compatibility
        "claim_amount": features["claim_am"],
        "time_of_day": features["time_of_c"],
        "location_risk": features["location_r"],
    }
    
    return feature_vector, feature_dict


def score_claim(claim_data: dict) -> dict:
    """
    Score a claim for fraud likelihood.
    
    Process:
    1. Load model (singleton - loads once)
    2. Extract features from claim_data
    3. Compute feature hash for audit trail
    4. Get fraud score from model
    5. Return score with metadata
    
    Args:
        claim_data: Dictionary with claim information
        
    Returns:
        {
            "score": float,           # 0.0-1.0 fraud likelihood
            "model_version": str,     # Model version used
            "feature_hash": str,      # SHA3 hash of features
            "features_used": list,    # List of feature names
            "timestamp": str          # ISO format timestamp
        }
        
    Raises:
        RuntimeError: If model fails to load or predict
    """
    try:
        # Load model (singleton - only loads once)
        loader = ModelLoader()
        model = loader.load_model()
        
        # Extract features
        feature_vector, feature_dict = extract_features(claim_data)
        
        # Compute feature hash for audit trail
        feature_json = json.dumps(feature_dict, sort_keys=True)
        feature_hash = crypto.hash_data(feature_json.encode()).hex()
        
        # Get prediction based on model type
        if MODEL_CONFIG["model_type"] == "isolation_forest":
            # Isolation Forest: -1 (anomaly) or 1 (normal)
            # Convert to 0.0-1.0 fraud score
            prediction = model.predict([feature_vector])[0]
            anomaly_score = model.score_samples([feature_vector])[0]
            
            if prediction == -1:
                # Anomaly detected
                fraud_score = 1.0
            else:
                # Normal - convert anomaly score to [0, 1]
                # Lower anomaly scores indicate higher fraud likelihood
                fraud_score = max(0.0, min(1.0, -anomaly_score))
        else:
            # XGBoost or other: direct probability
            if hasattr(model, "predict_proba"):
                fraud_score = float(model.predict_proba([feature_vector])[0][1])
            else:
                # Fallback for classifiers without predict_proba
                prediction = model.predict([feature_vector])[0]
                fraud_score = 1.0 if prediction == 1 else 0.0
        
        # Build result
        result = {
            "score": float(fraud_score),
            "model_version": loader._model_version,
            "feature_hash": feature_hash,
            "features_used": list(feature_dict.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        raise RuntimeError(f"Fraud scoring failed: {e}")


def score_and_log_claim(claim_id: str, claim_data: dict) -> dict:
    """
    Score claim and automatically log to tamper-evident log.
    
    Args:
        claim_id: Insurance claim identifier
        claim_data: Claim information dictionary
        
    Returns:
        Fraud score result dictionary with log_entry_id added
    """
    from append_log import add_log_event
    
    # Get fraud score
    score_result = score_claim(claim_data)
    
    # Log to tamper-evident log
    log_entry = add_log_event(
        claim_id=claim_id,
        event_type="fraud_score",
        event_data={
            "fraud_score": score_result["score"],
            "model_version": score_result["model_version"],
            "feature_hash": score_result["feature_hash"],
            "features_used": score_result["features_used"],
            "timestamp": score_result["timestamp"]
        }
    )
    
    # Add log entry ID to result
    score_result["log_entry_id"] = log_entry.id
    
    return score_result

