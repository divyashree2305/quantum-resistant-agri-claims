'use client';

/**
 * Security Context - Manages Kyber handshake state and security status
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { performHandshake } from '@/lib/api/handshake';
import type { HandshakeStatus } from '@/types';

interface SecurityContextType {
  status: HandshakeStatus;
  sessionToken: string | null;
  initiateHandshake: () => Promise<void>;
  reset: () => void;
  isSecure: boolean;
}

const SecurityContext = createContext<SecurityContextType | undefined>(undefined);

export function SecurityProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<HandshakeStatus>('idle');
  const [sessionToken, setSessionToken] = useState<string | null>(null);

  const initiateHandshake = useCallback(async () => {
    try {
      setStatus('initiating');

      // Perform handshake without sending a client key
      // Backend will generate a valid client keypair and return it
      const response = await performHandshake();

      // Store session token and client public key (returned by server)
      setSessionToken(response.session_token);
      
      // Note: The server generated the client keypair, so we store the public key
      // In production, integrate a real Kyber JS library to generate keys client-side
      if (typeof window !== 'undefined' && response.client_public_key) {
        localStorage.setItem('client_public_key', response.client_public_key);
      }
      
      setStatus('completed');

      // Note: In a real implementation with client-side key generation,
      // we would also decapsulate the shared secret using the ciphertext and private key here
    } catch (error) {
      console.error('Handshake failed:', error);
      // Log more details if available
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        console.error('Backend error detail:', axiosError.response?.data?.detail);
      }
      setStatus('error');
    }
  }, []);

  const reset = useCallback(() => {
    setStatus('idle');
    setSessionToken(null);
  }, []);

  const isSecure = status === 'completed' && sessionToken !== null;

  return (
    <SecurityContext.Provider
      value={{
        status,
        sessionToken,
        initiateHandshake,
        reset,
        isSecure,
      }}
    >
      {children}
    </SecurityContext.Provider>
  );
}

export function useSecurity() {
  const context = useContext(SecurityContext);
  if (context === undefined) {
    throw new Error('useSecurity must be used within a SecurityProvider');
  }
  return context;
}

