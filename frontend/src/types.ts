export interface UploadResponse {
  job_id: string;
  status: string;
  filename: string;
  total_findings: number;
  risk_score: number;
  risk_level: string;
}

export interface Finding {
  page: number;
  trap_type: 'instruction' | 'canary' | 'watermark' | 'obfuscation' | 'metadata_leak' | 'unknown';
  impact: 'critical' | 'high' | 'medium' | 'low' | 'info';
  hidden_text: string;
  decoded_text: string;
  detection_method: string;
  classification_reason: string;
  recommendation: string;
}

export interface AnalysisResponse {
  filename: string;
  total_pages: number;
  risk_score: number;
  risk_level: string;
  executive_summary: string;
  summary_by_type: Record<string, number>;
  findings: Finding[];
}
