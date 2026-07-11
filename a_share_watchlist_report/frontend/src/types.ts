export type ReportSummary = {
  exists: boolean;
  missing_files: string[];
  data_quality: { ok: boolean; errors?: string[]; warnings?: string[] };
  run_metrics?: Record<string, number | string | boolean>;
  row_counts: Record<string, number>;
  artifacts: Record<string, string>;
};

export type ReportRun = {
  id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  message: string | null;
};

export type ReportTable = {
  name: string;
  exists: boolean;
  columns: string[];
  row_count: number;
  filtered_count?: number;
  limit?: number;
  offset?: number;
  source?: string;
  updated_at?: string;
  rows: Record<string, string | number | boolean | null>[];
  errors: string[];
};

export type TableQuery = {
  limit?: number;
  offset?: number;
  search?: string;
  sortBy?: string;
  sortDir?: "asc" | "desc";
};

export type SecurityDetail = {
  symbol: string;
  exists: boolean;
  name: string;
  latest_review_label: string;
  latest_review_score: string;
  risk_flags: string;
  sections: Record<string, Record<string, string | number | boolean | null>[]>;
};
