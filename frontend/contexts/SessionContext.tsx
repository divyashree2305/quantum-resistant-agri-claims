'use client';

/**
 * Session Context - Manages authentication session state
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface SessionContextType {
  token: string | null;
  isValid: boolean;
  expiresAt: number | null;
  setToken: (token: string | null) => void;
  clearSession: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<number | null>(null);

  // Load session from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('session_token');
      const storedExpiresAt = localStorage.getItem('session_expires_at');
      
      if (storedToken) {
        setTokenState(storedToken);
      }
      
      if (storedExpiresAt) {
        const expires = parseInt(storedExpiresAt, 10);
        setExpiresAt(expires);
        
        // Check if expired
        if (expires < Date.now()) {
          clearSession();
        }
      }
    }
  }, []);

  const setToken = (newToken: string | null) => {
    setTokenState(newToken);
    
    if (typeof window !== 'undefined') {
      if (newToken) {
        localStorage.setItem('session_token', newToken);
        // Set expiration to 24 hours from now
        const expires = Date.now() + 24 * 60 * 60 * 1000;
        setExpiresAt(expires);
        localStorage.setItem('session_expires_at', expires.toString());
      } else {
        localStorage.removeItem('session_token');
        localStorage.removeItem('session_expires_at');
        setExpiresAt(null);
      }
    }
  };

  const clearSession = () => {
    setToken(null);
  };

  const isValid = token !== null && (expiresAt === null || expiresAt > Date.now());

  return (
    <SessionContext.Provider
      value={{
        token,
        isValid,
        expiresAt,
        setToken,
        clearSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

