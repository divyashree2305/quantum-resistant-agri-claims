/**
 * TypeScript type definitions for the Insurance Claim System
 */

// API Request/Response Types
export interface HandshakeRequest {
  client_public_key?: string; // base64 encoded, optional - server will generate if not provided
}

export interface HandshakeResponse {
  server_public_key: string; // base64 encoded
  client_public_key: string; // base64 encoded - returned so client can store it
  ciphertext: string; // base64 encoded
  session_token: string;
}

export interface ClaimSubmitRequest {
  claim_data: ClaimData;
}

export interface ClaimSubmitResponse {
  success: boolean;
  log_entry_id: number;
  fraud_score: number;
  model_version: string;
}

export interface ClaimData {
  claim_id?: string;
  claim_amount: number;
  timestamp: string;
  location: string;
  description?: string;
  [key: string]: any;
}

export interface CheckpointResponse {
  success: boolean;
  checkpoint_id: number;
  merkle_root: string;
  entries_range: string;
  epoch_id: string;
}

export interface VerifyCheckpointResponse {
  valid: boolean;
  checkpoint_id: number;
  epoch_id: string;
  message: string;
}

export interface ProveInclusionResponse {
  valid: boolean;
  log_entry_id: number;
  checkpoint_id: number;
  merkle_path: Array<{ node: string; direction: 'left' | 'right' }>;
}

export interface VerifyAIScoreResponse {
  valid: boolean;
  log_entry_id: number;
  feature_hash_match: boolean;
  model_version: string;
  message: string;
}

// User Role Types
export type UserRole = 'public' | 'adjuster' | 'admin' | 'auditor';

// Security Context Types
export type HandshakeStatus = 'idle' | 'initiating' | 'completed' | 'error';

export interface SecurityState {
  status: HandshakeStatus;
  sessionToken: string | null;
  clientPublicKey: Uint8Array | null;
  serverPublicKey: Uint8Array | null;
  ciphertext: Uint8Array | null;
}

// Session Context Types
export interface SessionState {
  token: string | null;
  isValid: boolean;
  expiresAt: number | null;
}

// Theme Types
export type ThemeMode = 'light' | 'dark';

// Language Types
export type Locale = 'en' | 'es';

// Claim Types
export interface Claim {
  id: string;
  claim_id: string;
  claim_amount: number;
  timestamp: string;
  location: string;
  description?: string;
  fraud_score: number;
  model_version: string;
  log_entry_id: number;
}

export interface Checkpoint {
  id: number;
  merkle_root: string;
  entries_range: string;
  prev_checkpoint_hash: string | null;
  signer_id: string;
  created_at: string;
}

