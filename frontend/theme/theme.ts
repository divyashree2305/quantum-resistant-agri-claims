/**
 * Material-UI theme configuration (minimalist, Apple-inspired design)
 */

import { createTheme, ThemeOptions } from '@mui/material/styles';
import { lightPalette, darkPalette } from './palette';

const typography = {
  fontFamily: [
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  h1: {
    fontSize: '32px',
    fontWeight: 700,
    lineHeight: 1.2,
  },
  h2: {
    fontSize: '24px',
    fontWeight: 600,
    lineHeight: 1.3,
  },
  h3: {
    fontSize: '20px',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  body1: {
    fontSize: '16px',
    fontWeight: 400,
    lineHeight: 1.5,
  },
  body2: {
    fontSize: '14px',
    fontWeight: 400,
    lineHeight: 1.5,
  },
  caption: {
    fontSize: '14px',
    fontWeight: 400,
    lineHeight: 1.4,
  },
};

const commonThemeOptions: ThemeOptions = {
  typography,
  shape: {
    borderRadius: 8,
  },
  spacing: 8, // Base spacing unit (8px)
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          padding: '10px 24px',
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
};

export const lightTheme = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'light',
    ...lightPalette,
  },
});

export const darkTheme = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'dark',
    ...darkPalette,
  },
  components: {
    ...commonThemeOptions.components,
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
        },
      },
    },
  },
});

