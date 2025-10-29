"""
Model Configuration for AI Fraud Detection

Defines model metadata, paths, and expected features.
"""

MODEL_CONFIG = {
    "model_path": "ai/fraud_model.pkl",
    "model_version": "model_v1",
    "model_type": "xgboost",  # Your model is XGBClassifier
}

# Expected features - flexible approach
# These are the features the model expects based on training data
# Model was trained with: claim_am, time_of_c, location_r, is_fraud
# We map these to the feature extraction:
FEATURE_MAPPING = {
    "claim_am": "claim_amount",
    "time_of_c": "time_of_day", 
    "location_r": "location_risk",
}

# Actual features used by the model (3 features in order)
EXPECTED_FEATURES = [
    "claim_am",      # Claim amount (from training data)
    "time_of_c",    # Time of day (hour) (from training data)
    "location_r",   # Location risk score (from training data)
]

