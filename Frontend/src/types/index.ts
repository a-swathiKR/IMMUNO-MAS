export interface Agent {
  id: string;
  agent_id: string;
  name: string;
  role: string;
  status: string;
  raw_status: string;
  designation: string;
  warn_count: number;
  total_warnings: number;
  total_quarantines: number;
  is_active_backup: boolean;
  available: boolean;
}

export interface HealthResponse {
  status?: string;
  message?: string;
  version?: string;
  system?: string;
  timestamp?: string;
  [key: string]: unknown;
}
