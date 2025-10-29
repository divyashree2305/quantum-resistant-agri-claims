'use client';

/**
 * Security Badge - Visual indicator of handshake status
 * Shows "Post-Quantum Secure" badge when handshake is completed
 */

import React from 'react';
import { Chip } from '@mui/material';
import { Security, LockOpen, Warning, CheckCircle } from '@mui/icons-material';
import { useSecurity } from '@/contexts/SecurityContext';

export function SecurityBadge() {
  const { status } = useSecurity();

  const getBadgeProps = () => {
    switch (status) {
      case 'completed':
        return {
          label: 'Post-Quantum Secure',
          icon: <CheckCircle fontSize="small" />,
          color: 'success' as const,
        };
      case 'initiating':
        return {
          label: 'Establishing Secure Connection...',
          icon: <Security fontSize="small" />,
          color: 'warning' as const,
        };
      case 'error':
        return {
          label: 'Connection Insecure',
          icon: <Warning fontSize="small" />,
          color: 'error' as const,
        };
      default:
        return {
          label: 'Not Secure',
          icon: <LockOpen fontSize="small" />,
          color: 'default' as const,
        };
    }
  };

  const badgeProps = getBadgeProps();

  return (
    <Chip
      {...badgeProps}
      size="small"
      sx={{
        fontWeight: 500,
        '& .MuiChip-icon': {
          marginLeft: '8px',
        },
      }}
    />
  );
}

