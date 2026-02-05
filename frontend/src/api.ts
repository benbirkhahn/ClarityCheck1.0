import type { UploadResponse, AnalysisResponse, JobStatusResponse } from './types';

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

export async function getJob(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!response.ok) throw new Error(`Failed to get job: ${response.statusText}`);
  return response.json();
}

export async function pollJobStatus(jobId: string): Promise<JobStatusResponse> {
  const POLL_INTERVAL = 2000;
  const MAX_ATTEMPTS = 60; // 2 minutes timeout

  for (let i = 0; i < MAX_ATTEMPTS; i++) {
    const job = await getJob(jobId);

    if (job.status === 'completed') return job;
    if (job.status === 'failed') throw new Error(job.error || 'Job failed');

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
  }

  throw new Error('Analysis timed out');
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
