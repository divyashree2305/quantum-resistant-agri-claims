'use client';

/**
 * Claim Status Page - Check status of submitted claims
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
  Card,
  CardContent,
  Chip,
  Divider,
} from '@mui/material';
import { Search, Verified, Error as ErrorIcon } from '@mui/icons-material';
import { getClaimStatus } from '@/lib/api/claims';
import { useSecurity } from '@/contexts/SecurityContext';
import { formatFraudScore, getFraudScoreColor } from '@/lib/utils/formatters';

export default function ClaimStatusPage() {
  const { isSecure, initiateHandshake, status } = useSecurity();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [claimStatus, setClaimStatus] = useState<{
    log_entry_id: number;
    claim_id: string;
    event_type: string;
    timestamp: string;
    fraud_score: number | null;
    model_version: string | null;
    tamper_verified: boolean;
  } | null>(null);
  
  const [logEntryId, setLogEntryId] = useState<string>('');

  useEffect(() => {
    // Auto-initiate handshake if not secure
    if (!isSecure && status === 'idle') {
      initiateHandshake();
    }
  }, [isSecure, status, initiateHandshake]);

  const handleSearch = async () => {
    if (!logEntryId.trim()) {
      setError('Please enter a log entry ID');
      return;
    }

    const entryId = parseInt(logEntryId.trim(), 10);
    if (isNaN(entryId) || entryId <= 0) {
      setError('Log entry ID must be a positive number');
      return;
    }

    setLoading(true);
    setError(null);
    setClaimStatus(null);

    try {
      if (!isSecure) {
        throw new Error('Secure connection not established. Please wait...');
      }

      const status = await getClaimStatus(entryId);
      setClaimStatus(status);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : (err as { response?: { data?: { detail?: string } } }).response?.data?.detail 
          || 'Failed to fetch claim status';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleSearch();
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Check Claim Status
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Enter the log entry ID from your claim submission to check its status and verify integrity.
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <TextField
            fullWidth
            label="Log Entry ID"
            value={logEntryId}
            onChange={(e) => setLogEntryId(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter log entry ID (e.g., 1, 2, 3...)"
            type="number"
            disabled={loading || !isSecure}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: 'action.active' }} />,
            }}
          />
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={loading || !isSecure || !logEntryId.trim()}
            sx={{ minWidth: 120 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Search'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {claimStatus && (
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Claim Status</Typography>
                <Chip
                  icon={claimStatus.tamper_verified ? <Verified /> : <ErrorIcon />}
                  label={claimStatus.tamper_verified ? 'Verified' : 'Not Verified'}
                  color={claimStatus.tamper_verified ? 'success' : 'warning'}
                  size="small"
                />
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Log Entry ID
                  </Typography>
                  <Typography variant="body1">{claimStatus.log_entry_id}</Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Claim ID
                  </Typography>
                  <Typography variant="body1">{claimStatus.claim_id}</Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Event Type
                  </Typography>
                  <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
                    {claimStatus.event_type.replace('_', ' ')}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Timestamp
                  </Typography>
                  <Typography variant="body1">
                    {new Date(claimStatus.timestamp).toLocaleString()}
                  </Typography>
                </Box>

                {claimStatus.fraud_score !== null && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Fraud Score
                    </Typography>
                    <Typography
                      variant="body1"
                      sx={{
                        color: getFraudScoreColor(claimStatus.fraud_score),
                        fontWeight: 'bold',
                      }}
                    >
                      {formatFraudScore(claimStatus.fraud_score)}
                    </Typography>
                  </Box>
                )}

                {claimStatus.model_version && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Model Version
                    </Typography>
                    <Typography variant="body1">{claimStatus.model_version}</Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        )}

        {!isSecure && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Establishing secure connection...
          </Alert>
        )}
      </Paper>
    </Container>
  );
}
