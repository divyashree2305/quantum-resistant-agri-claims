'use client';

import  { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { performHandshake } from '@/lib/api/handshake';
import { useActivityLog } from '@/contexts/ActivityContext';
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
  const { addActivity, updateActivity } = useActivityLog();

  const initiateHandshake = useCallback(async () => {
    const handshakeId = `handshake-${Date.now()}`;
    
    try {
      setStatus('initiating');

      // Log handshake initiation
      addActivity({
        type: 'handshake',
        title: 'Kyber KEM Handshake Initiated',
        description: 'Starting post-quantum secure key exchange (ML-KEM-1024)',
        status: 'pending',
        details: 'Establishing secure channel using Kyber key encapsulation mechanism...',
      });

      // Perform handshake without sending a client key
      // Backend will generate a valid client keypair and return it
      addActivity({
        type: 'handshake',
        title: 'Generating Client Keypair',
        description: 'Server generating client Kyber keypair (ML-KEM-1024)',
        status: 'pending',
        details: 'Creating 1568-byte public key and 3168-byte private key...',
      });

      const response = await performHandshake();

      updateActivity(handshakeId, {
        status: 'completed',
        description: 'Client keypair generated successfully',
      });

      addActivity({
        type: 'handshake',
        title: 'Server Keypair Generated',
        description: 'Server generated its own Kyber keypair',
        status: 'completed',
        details: {
          server_public_key_length: response.server_public_key.length,
          client_public_key_length: response.client_public_key.length,
          ciphertext_length: response.ciphertext.length,
        },
      });

      addActivity({
        type: 'handshake',
        title: 'Shared Secret Encapsulated',
        description: 'Server encapsulated shared secret using client public key',
        status: 'completed',
        details: 'ML-KEM-1024 encapsulation successful. Shared secret established.',
      });

      // Store session token and client public key (returned by server)
      setSessionToken(response.session_token);
      
      if (typeof window !== 'undefined' && response.client_public_key) {
        localStorage.setItem('client_public_key', response.client_public_key);
      }
      
      addActivity({
        type: 'handshake',
        title: 'Session Established',
        description: 'Post-quantum secure session created',
        status: 'completed',
        details: {
          session_token: response.session_token.substring(0, 20) + '...',
          security_level: 'Post-Quantum (ML-KEM-1024)',
        },
      });
      
      setStatus('completed');
    } catch (error) {
      console.error('Handshake failed:', error);
      const errorDetail = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Unknown error';
      
      addActivity({
        type: 'handshake',
        title: 'Handshake Failed',
        description: `Error: ${errorDetail || 'Connection failed'}`,
        status: 'error',
        details: errorDetail,
      });
      
      setStatus('error');
    }
  }, [addActivity, updateActivity]);

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

