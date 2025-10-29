'use client';

/**
 * Error Boundary Component for catching React errors
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { ErrorOutline } from '@mui/icons-material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="sm">
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '50vh',
              gap: 2,
            }}
          >
            <ErrorOutline color="error" sx={{ fontSize: 64 }} />
            <Typography variant="h5" component="h1">
              Something went wrong
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              {this.state.error?.message || 'An unexpected error occurred'}
            </Typography>
            <Button
              variant="contained"
              onClick={() => window.location.reload()}
              sx={{ mt: 2 }}
            >
              Reload Page
            </Button>
          </Box>
        </Container>
      );
    }

    return this.props.children;
  }
}

