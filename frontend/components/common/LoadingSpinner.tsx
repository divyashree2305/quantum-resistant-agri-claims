'use client';

/**
 * Loading Spinner Component
 */

import React from 'react';
import { CircularProgress, Box } from '@mui/material';

interface LoadingSpinnerProps {
  size?: number;
  fullScreen?: boolean;
}

export function LoadingSpinner({ size = 40, fullScreen = false }: LoadingSpinnerProps) {
  if (fullScreen) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          width: '100%',
        }}
      >
        <CircularProgress size={size} />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 4,
      }}
    >
      <CircularProgress size={size} />
    </Box>
  );
}

