'use client';

/**
 * Theme Context - Manages dark/light mode and theme preferences
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { ThemeMode } from '@/types';

interface ThemeContextType {
  mode: ThemeMode;
  toggleTheme: () => void;
  setMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>('light');

  // Load theme preference from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedMode = localStorage.getItem('theme_mode') as ThemeMode | null;
      if (savedMode && (savedMode === 'light' || savedMode === 'dark')) {
        setModeState(savedMode);
      } else {
        // Detect system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setModeState(prefersDark ? 'dark' : 'light');
      }
    }
  }, []);

  // Save theme preference to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme_mode', mode);
      document.documentElement.classList.toggle('dark', mode === 'dark');
    }
  }, [mode]);

  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode);
  };

  const toggleTheme = () => {
    setModeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider
      value={{
        mode,
        toggleTheme,
        setMode,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

