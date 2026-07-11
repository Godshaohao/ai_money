import type { ReportRun, ReportSummary, ReportTable, SecurityDetail, TableQuery } from "./types";

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function fetchSummary(): Promise<ReportSummary> {
  return getJson<ReportSummary>("/api/report/summary");
}

export function fetchRuns(): Promise<{ runs: ReportRun[] }> {
  return getJson<{ runs: ReportRun[] }>("/api/report/runs");
}

export function fetchTable(name: string, query: TableQuery = {}): Promise<ReportTable> {
  const params = new URLSearchParams();
  if (query.limit !== undefined) params.set("limit", String(query.limit));
  if (query.offset !== undefined) params.set("offset", String(query.offset));
  if (query.search) params.set("search", query.search);
  if (query.sortBy) params.set("sort_by", query.sortBy);
  if (query.sortDir) params.set("sort_dir", query.sortDir);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return getJson<ReportTable>(`/api/report/tables/${name}${suffix}`);
}

export function fetchSecurityDetail(symbol: string): Promise<SecurityDetail> {
  return getJson<SecurityDetail>(`/api/report/securities/${symbol}`);
}

export async function refreshReport(): Promise<{ status: string; summary: ReportSummary }> {
  const response = await fetch("/api/report/run", { method: "POST" });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<{ status: string; summary: ReportSummary }>;
}
