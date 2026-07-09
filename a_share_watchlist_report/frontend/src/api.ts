import type { ReportRun, ReportSummary, ReportTable } from "./types";

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

export function fetchTable(name: string): Promise<ReportTable> {
  return getJson<ReportTable>(`/api/report/tables/${name}`);
}

export async function refreshReport(): Promise<{ status: string; summary: ReportSummary }> {
  const response = await fetch("/api/report/run", { method: "POST" });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<{ status: string; summary: ReportSummary }>;
}
