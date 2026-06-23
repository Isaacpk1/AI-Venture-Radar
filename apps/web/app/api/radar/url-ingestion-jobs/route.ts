import { proxyRadarRequest } from "@/lib/api/radar-server";

export async function POST(request: Request) {
  const body = await request.text();
  return proxyRadarRequest("/url-ingestion/jobs", { method: "POST", body });
}
