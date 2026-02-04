import { UploadResponse, AnalysisResponse } from './types';

const API_BASE = 'http://127.0.0.1:8000/api';

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getAnalysis(jobId: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/analysis`);
  
  if (!response.ok) {
    throw new Error(`Failed to get analysis: ${response.statusText}`);
  }

  return response.json();
}

export async function downloadSanitized(jobId: string, filename: string): Promise<void> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/sanitize`);
  
  if (!response.ok) {
    throw new Error(`Failed to sanitize: ${response.statusText}`);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sanitized_${filename}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}
