import type {
  ReportRun,
  ReportSummary,
  ReportTable,
  SecurityDetail,
  SectorWorkbench,
  StockAnalysisResponse,
  StrategyCandidates,
  StrategyDetail,
  StrategyRun,
  TableQuery
} from "./types";

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

export function fetchStrategyRuns(): Promise<{ runs: StrategyRun[] }> {
  return getJson<{ runs: StrategyRun[] }>("/api/strategy/runs");
}

export function fetchStrategyCandidates(query: TableQuery & { module?: string } = {}): Promise<StrategyCandidates> {
  const params = new URLSearchParams();
  if (query.limit !== undefined) params.set("limit", String(query.limit));
  if (query.offset !== undefined) params.set("offset", String(query.offset));
  if (query.search) params.set("search", query.search);
  if (query.sortBy) params.set("sort_by", query.sortBy);
  if (query.sortDir) params.set("sort_dir", query.sortDir);
  if (query.module) params.set("module", query.module);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return getJson<StrategyCandidates>(`/api/strategy/candidates${suffix}`);
}

export function fetchStrategyDetail(symbol: string): Promise<StrategyDetail> {
  return getJson<StrategyDetail>(`/api/strategy/securities/${symbol}`);
}

export function fetchSectorWorkbench(): Promise<SectorWorkbench> {
  return getJson<SectorWorkbench>("/api/analysis/sectors");
}

export function fetchStockAnalysis(symbol: string): Promise<StockAnalysisResponse> {
  return getJson<StockAnalysisResponse>(`/api/analysis/stocks/${symbol}`);
}

export async function refreshReport(): Promise<{ status: string; summary: ReportSummary }> {
  const response = await fetch("/api/report/run", { method: "POST" });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<{ status: string; summary: ReportSummary }>;
}
