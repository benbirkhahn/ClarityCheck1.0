import type { UploadResponse, AnalysisResponse, JobStatusResponse } from './types';

const ENV_API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
const API_BASE = ENV_API_URL.endsWith('/api') ? ENV_API_URL : `${ENV_API_URL}/api`;

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

export async function downloadSanitized(
  jobId: string,
  filename: string,
  confirmedFindingIds?: string[],
  manualRegions?: Array<{ id: string, page: number, x: number, y: number, width: number, height: number }>
): Promise<void> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/sanitize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      confirmed_finding_ids: confirmedFindingIds,
      manual_regions: manualRegions
    }),
  });

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

export async function getUsage(): Promise<{
  plan: string;
  limit: number;
  usage: number;
  can_upload: boolean;
  remaining?: number;
}> {
  const response = await fetch(`${API_BASE}/usage`);
  if (!response.ok) throw new Error(`Failed to get usage: ${response.statusText}`);
  const json = await response.json();
  return json.data;
}

export async function createCheckoutSession(priceId: string): Promise<{ url: string }> {
  /* 
     We need a user_id. 
     For now, we use the specific fingerprint logic or a stored ID.
     The backend fingerprint logic generates ID from request headers if not provided.
     But for checkout, we likely need to pass the client_reference_id which matches the user. 
     
     WAIT: The backend `create_checkout_session` expects `user_id` in the body.
     Our frontend doesn't strictly know its "fingerprint" ID because it's generated on the server.
     
     SOLUTION: 
     1. We should probably return the `user_id` from the `getUsage` endpoint so the frontend knows it.
     2. OR, the backend endpoint should infer user_id from the request (headers) if not provided.
     
     Let's look at `usage_routes.py` and `subscriptions.py` again.
     `subscriptions.py` takes `CheckoutSessionRequest(price_id: str, user_id: str)`.
     
     I need to modify `api.ts` to get the `user_id` first?
     
     Actually, `getUsage` returns `plan`, `limit`, etc. I should check if it returns `user_id`.
     If not, I should update `getUsage` (backend) to return it, OR update `create_checkout_session` (backend) to optionally take `user_id` or derive it.
     
     Let's assume for now I should update `getUsage` to return `user_id` or just fetch it.
     Actually, looking at `usage_routes.py` (from memory):
     It uses `get_user_id(request)`.
     
     If I change `subscriptions.py` to use `get_user_id(request)` if `user_id` is missing in body?
     That would be safer/easier.
     
     But I can't easily change backend right now without deploying.
     
     Let's check `getUsage` response in `api.ts`.
     It returns `json.data`.
     
     Let's blindly assume I can get `user_id` from somewhere or make the backend derive it.
     
     Actually, the cleanest way is:
     The frontend calls `getUsage`. Does `getUsage` return `user_id`?
     Let's check `backend/api/usage_routes.py`.
  */
  // Temporary: Generate a fingerprint or fetch it.
  // Ideally, the backend `create_checkout_session` should handle the identity.
  // Let's check `subscriptions.py` again to be sure what it expects.
  // It expects `CheckoutSessionRequest`.

  // Update: I will implements a helper to get the user ID, or pass a dummy if the backend handles it.
  // Let's peek at `backend/api/usage_routes.py` and `backend/api/subscriptions.py` to confirm.

  const response = await fetch(`${API_BASE}/create-checkout-session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      price_id: priceId,
      // user_id is optional, backend will derive from request fingerprint if missing
    }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create checkout session');
  }

  return response.json();
}
