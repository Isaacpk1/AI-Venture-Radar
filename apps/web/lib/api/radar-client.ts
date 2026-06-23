import type {
  Briefing,
  CreateUrlIngestionJobInput,
  Recommendation,
  Startup,
  StartupEvidence,
  UrlIngestionJob,
} from "./radar-types";

export class RadarApiError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "content-type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new RadarApiError(body?.detail ?? "Nao foi possivel comunicar com a API.", response.status);
  }
  return response.json() as Promise<T>;
}

export function createUrlIngestionJob(input: CreateUrlIngestionJobInput) {
  return request<UrlIngestionJob>("/api/radar/url-ingestion-jobs", { method: "POST", body: JSON.stringify(input) });
}

export function getUrlIngestionJob(jobId: string) {
  return request<UrlIngestionJob>(`/api/radar/url-ingestion-jobs/${jobId}`);
}

export function getStartup(startupId: string) {
  return request<Startup>(`/api/radar/startups/${startupId}`);
}

export function getStartupEvidences(startupId: string) {
  return request<StartupEvidence[]>(`/api/radar/startups/${startupId}/evidences`);
}

export function listRecommendations(startupId: string) {
  return request<Recommendation[]>(`/api/radar/recommendations?startup_id=${encodeURIComponent(startupId)}`);
}

export function listBriefings(startupId: string) {
  return request<Briefing[]>(`/api/radar/briefings?startup_id=${encodeURIComponent(startupId)}`);
}

export async function refreshStartupAnalysis(startupId: string) {
  await request<Recommendation[]>("/api/radar/recommendations", {
    method: "POST",
    body: JSON.stringify({ startup_id: startupId }),
  });
  return request<Briefing>("/api/radar/briefings", {
    method: "POST",
    body: JSON.stringify({ startup_id: startupId }),
  });
}
