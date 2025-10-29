# AI Model Integration Guide

## Model Training Data Format

Your model was trained with the following data structure:

| Feature Name | Description | Data Type | Example |
|-------------|-------------|-----------|---------|
| `claim_am` | Claim amount | float | 320.11 |
| `time_of_c` | Time of day (hour 0-23) | int | 14 |
| `location_r` | Location risk score (0.0-1.0) | float | 0.22 |
| `is_fraud` | Fraud indicator (target) | int (0/1) | 0 |

## Current Implementation

The AI fraud detection module has been updated to support your model's exact training format:

### 1. Configuration (`ai/config.py`)

```python
# Model expects exactly 3 features in this order:
EXPECTED_FEATURES = [
    "claim_am",      # Claim amount
    "time_of_c",     # Time of day (hour)
    "location_r",    # Location risk score
]
```

### 2. Feature Mapping

The implementation supports both **training feature names** and **user-friendly names**:

**Training Names** → **User-Friendly Names**
- `claim_am` → `claim_amount`
- `time_of_c` → `time_of_day`
- `location_r` → `location_risk`

### 3. Usage Examples

#### Using Training Feature Names (Direct)
```python
from ai.ai_score import score_and_log_claim

result = score_and_log_claim(
    claim_id="CLAIM-123",
    claim_data={
        "claim_am": 320.11,      # Direct training feature name
        "time_of_c": 14,         # Direct training feature name
        "location_r": 0.22       # Direct training feature name
    }
)
```

#### Using User-Friendly Names (Automatic Mapping)
```python
result = score_and_log_claim(
    claim_id="CLAIM-123",
    claim_data={
        "claim_amount": 320.11,  # Mapped to claim_am
        "time_of_day": 14,      # Mapped to time_of_c
        "location_risk": 0.22   # Mapped to location_r
    }
)
```

#### Using Timestamp (Auto-extraction)
```python
result = score_and_log_claim(
    claim_id="CLAIM-123",
    claim_data={
        "claim_amount": 320.11,
        "timestamp": "2025-10-15T14:30:00",  # Hour 14 extracted automatically
        "location_risk": 0.22
    }
)
```

### 4. Feature Extraction Logic

The `extract_features()` function:

1. **Accepts both naming conventions** (training names or user-friendly names)
2. **Extracts hour from timestamps** if provided
3. **Provides defaults** for missing features:
   - `time_of_c`: Defaults to 12 (noon)
   - `location_r`: Defaults to 0.5 (medium risk)
4. **Returns exactly 3 features** in the order expected by your model

### 5. Model Compatibility

Your model file (`ai/fraud_model.pkl`) should:
- Accept numpy array of shape `(1, 3)` or `(3,)`
- Return predictions compatible with scikit-learn interface
- Support either:
  - Isolation Forest: Uses `predict()` and `score_samples()`
  - Other models: Uses `predict_proba()` if available

### 6. Testing

All tests now use your model's 3-feature format:

```python
# Test with training data format
claim_data = {
    "claim_am": 320.11,
    "time_of_c": 14,
    "location_r": 0.22
}

# Feature vector will be: [320.11, 14, 0.22]
```

### 7. Integration with Tamper-Evident Logging

All fraud scores are automatically logged to the tamper-evident log with:
- Feature values (in both naming conventions)
- Feature hash (SHA3-256 of feature dict)
- Model version
- Timestamp
- Fraud score

This provides a complete audit trail for compliance and verification.

## Summary

✅ **Model Format Support**: 3 features (`claim_am`, `time_of_c`, `location_r`)  
✅ **Flexible Input**: Accepts training names or user-friendly names  
✅ **Default Handling**: Sensible defaults for missing features  
✅ **Timestamp Support**: Auto-extracts hour from ISO timestamps  
✅ **Tamper-Evident Logging**: All scores logged with feature hashes  
✅ **Comprehensive Testing**: All tests updated to use correct format  

Your trained model is ready to use with the implemented fraud detection system!

