/**
 * Home Page
 */

'use client';

import React, { useEffect } from 'react';
import { Container, Typography, Button, Box } from '@mui/material';
import { useSecurity } from '@/contexts/SecurityContext';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const { initiateHandshake, isSecure } = useSecurity();
  const router = useRouter();

  useEffect(() => {
    // Auto-initiate handshake on page load
    if (!isSecure) {
      initiateHandshake();
    }
  }, [isSecure, initiateHandshake]);

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '80vh',
          gap: 3,
          textAlign: 'center',
        }}
      >
        <Typography variant="h3" component="h1" gutterBottom>
          Post-Quantum Secure Insurance Claim System
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Submit and manage insurance claims with post-quantum cryptographic security
          and AI-driven fraud detection.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => router.push('/submit-claim')}
          >
            Submit Claim
          </Button>
          <Button
            variant="outlined"
            size="large"
            onClick={() => router.push('/claim-status')}
          >
            Check Status
          </Button>
        </Box>
      </Box>
    </Container>
  );
}
