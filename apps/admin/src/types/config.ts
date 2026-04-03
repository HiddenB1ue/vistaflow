export type CredentialHealth = 'healthy' | 'expired';

export interface ApiCredential {
  id: string;
  name: string;
  description: string;
  health: CredentialHealth;
  maskedKey: string;
  quotaInfo?: string;
  expiryWarning?: string;
}

export interface GlobalToggle {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}
