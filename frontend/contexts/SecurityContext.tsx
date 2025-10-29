'use client';

/**
 * Security Context - Manages Kyber handshake state and security status
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { performHandshake } from '@/lib/api/handshake';
import { generateClientKeyPair, encodeBase64, decodeBase64 } from '@/lib/utils/crypto-client';
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

      // Generate client Kyber keypair
      const { publicKey } = await generateClientKeyPair();

      // Validate key length
      if (publicKey.length !== 1568) {
        throw new Error(`Invalid public key length: expected 1568 bytes, got ${publicKey.length}`);
      }

      // Encode public key to base64
      const publicKeyBase64 = encodeBase64(publicKey);

      // Log for debugging (remove in production)
      console.log('Handshake: Generated public key length:', publicKey.length);
      console.log('Handshake: Base64 length:', publicKeyBase64.length);

      // Perform handshake with backend
      const response = await performHandshake(publicKeyBase64);

      // Store session token
      setSessionToken(response.session_token);
      setStatus('completed');

      // Note: In a real implementation, we would also decapsulate the shared secret
      // using the ciphertext and private key here
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

