'use client';

/**
 * Providers Component - Combines all context providers
 */

import React from 'react';
import { ThemeProvider as MUIThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import { SessionProvider } from '@/contexts/SessionContext';
import { SecurityProvider } from '@/contexts/SecurityContext';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { lightTheme, darkTheme } from '@/theme/theme';

// Emotion cache for MUI
const cache = createCache({ key: 'css', prepend: true });

function ThemedApp({ children }: { children: React.ReactNode }) {
  const { mode } = useTheme();
  const theme = mode === 'dark' ? darkTheme : lightTheme;

  return (
    <CacheProvider value={cache}>
      <MUIThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MUIThemeProvider>
    </CacheProvider>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <SessionProvider>
        <SecurityProvider>
          <ThemeProvider>
            <LanguageProvider>
              <ThemedApp>{children}</ThemedApp>
            </LanguageProvider>
          </ThemeProvider>
        </SecurityProvider>
      </SessionProvider>
    </ErrorBoundary>
  );
}

