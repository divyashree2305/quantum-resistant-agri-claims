'use client';

/**
 * Claim Submission Page
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { submitClaim } from '@/lib/api/claims';
import { useSecurity } from '@/contexts/SecurityContext';
import { formatFraudScore, getFraudScoreColor } from '@/lib/utils/formatters';
import {
  validateClaimAmount,
  validateTimestamp,
  validateLocation,
  validateClaimId,
} from '@/lib/utils/validators';
import type { ClaimData } from '@/types';

export default function SubmitClaimPage() {
  const { isSecure, initiateHandshake, status } = useSecurity();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fraudScore, setFraudScore] = useState<number | null>(null);
  const [logEntryId, setLogEntryId] = useState<number | null>(null);

  const [formData, setFormData] = useState<ClaimData>({
    claim_amount: 0,
    timestamp: new Date().toISOString(),
    location: '',
    description: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Auto-initiate handshake if not secure
    if (!isSecure && status === 'idle') {
      initiateHandshake();
    }
  }, [isSecure, status, initiateHandshake]);

  const handleChange = (field: keyof ClaimData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'claim_amount' ? parseFloat(e.target.value) || 0 : e.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    const amountError = validateClaimAmount(formData.claim_amount);
    if (amountError) newErrors.claim_amount = amountError;

    const timestampError = validateTimestamp(formData.timestamp);
    if (timestampError) newErrors.timestamp = timestampError;

    const locationError = validateLocation(formData.location);
    if (locationError) newErrors.location = locationError;

    if (formData.claim_id) {
      const claimIdError = validateClaimId(formData.claim_id);
      if (claimIdError) newErrors.claim_id = claimIdError;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!validateForm()) {
      return;
    }

    if (!isSecure) {
      setError('Please wait for secure connection to be established.');
      return;
    }

    setLoading(true);

    try {
      const response = await submitClaim(formData);
      setSuccess(true);
      setFraudScore(response.fraud_score);
      setLogEntryId(response.log_entry_id);
      
      // Reset form
      setFormData({
        claim_amount: 0,
        timestamp: new Date().toISOString(),
        location: '',
        description: '',
      });
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(error.response?.data?.detail || error.message || 'Failed to submit claim');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Submit Insurance Claim
        </Typography>

        {!isSecure && status === 'initiating' && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Establishing secure connection...
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && fraudScore !== null && (
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body1" gutterBottom>
              Claim submitted successfully!
            </Typography>
            <Typography variant="body2">
              Log Entry ID: {logEntryId}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mt: 1,
                color: getFraudScoreColor(fraudScore),
                fontWeight: 'bold',
              }}
            >
              Fraud Score: {formatFraudScore(fraudScore)}
            </Typography>
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Claim ID (Optional)"
            value={formData.claim_id || ''}
            onChange={handleChange('claim_id')}
            margin="normal"
            error={!!errors.claim_id}
            helperText={errors.claim_id}
          />

          <TextField
            fullWidth
            label="Claim Amount"
            type="number"
            value={formData.claim_amount}
            onChange={handleChange('claim_amount')}
            margin="normal"
            required
            error={!!errors.claim_amount}
            helperText={errors.claim_amount}
            inputProps={{ min: 0, step: 0.01 }}
          />

          <TextField
            fullWidth
            label="Timestamp"
            type="datetime-local"
            value={formData.timestamp.slice(0, 16)}
            onChange={(e) => {
              const date = new Date(e.target.value).toISOString();
              const syntheticEvent = {
                target: { value: date },
              } as React.ChangeEvent<HTMLInputElement>;
              handleChange('timestamp')(syntheticEvent);
            }}
            margin="normal"
            required
            error={!!errors.timestamp}
            helperText={errors.timestamp}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            fullWidth
            label="Location"
            value={formData.location}
            onChange={handleChange('location')}
            margin="normal"
            required
            error={!!errors.location}
            helperText={errors.location}
          />

          <TextField
            fullWidth
            label="Description (Optional)"
            value={formData.description || ''}
            onChange={handleChange('description')}
            margin="normal"
            multiline
            rows={4}
          />

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={loading || !isSecure}
              sx={{ flex: 1 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Submit Claim'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Container>
  );
}

