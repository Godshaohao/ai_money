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

export type StrategyRun = {
  id: number;
  strategy_name: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  message: string | null;
  params: Record<string, unknown>;
  metrics: Record<string, number | string | boolean>;
};

export type StrategyCandidate = {
  id: number;
  run_id: number;
  module: string;
  symbol: string;
  name: string;
  score: number;
  label: string;
  risk_flags: string;
  reason: string;
  source_table: string;
  source_row: Record<string, string | number | boolean | null>;
};

export type StrategyCandidates = {
  run_id: number | null;
  row_count: number;
  filtered_count: number;
  limit: number;
  offset: number;
  rows: StrategyCandidate[];
};

export type StrategyEvidence = {
  id: number;
  run_id: number;
  symbol: string;
  module: string;
  evidence_type: string;
  title: string;
  detail: string;
  payload: Record<string, string | number | boolean | null>;
};

export type StrategyDetail = {
  symbol: string;
  exists: boolean;
  candidates: StrategyCandidate[];
  evidence: StrategyEvidence[];
};

export type SectorLeader = {
  symbol: string;
  name: string;
};

export type SectorCard = {
  trade_date: string;
  industry: string;
  limit_up_count: number;
  first_board_count: number;
  second_board_count: number;
  high_board_count: number;
  max_streak_count: number;
  broken_count: number;
  total_amount: number;
  leader_symbols: string[];
  leader_names: string[];
  leaders: SectorLeader[];
  echelon_summary: string;
  risk_flags: string[];
};

export type SectorWorkbench = {
  latest_trade_date: string;
  summary: {
    sector_count: number;
    limit_up_count: number;
    broken_count: number;
    high_board_count: number;
  };
  cards: SectorCard[];
  errors: string[];
};

export type StockDataAvailability = {
  price_history_available: boolean;
  limit_up_event_count: number;
  sector_event_count: number;
  strategy_candidate_count: number;
  review_record_count: number;
  dragon_tiger_count: number;
  missing_notes: string[];
};

export type StockEventTimelineItem = {
  trade_date: string;
  event_profile: string;
  streak_count: number;
  break_count: number;
  first_limit_time: string;
  last_limit_time: string;
  close: number | null;
  change_pct: number | null;
  change_pct_text: string;
  turnover_rate: number | null;
  turnover_rate_text: string;
  amount: number | null;
  amount_text: string;
  seal_amount: number | null;
  seal_amount_text: string;
  limit_up_stats: string;
  close_change_from_previous_event_pct: number | null;
  close_change_from_previous_event_text: string;
};

export type StockSectorPosition = {
  trade_date?: string;
  industry: string;
  position_summary: string;
  limit_up_count: number;
  first_board_count?: number;
  second_board_count?: number;
  high_board_count?: number;
  max_streak_count?: number;
  broken_count?: number;
  broken_ratio_pct: number;
  leader_symbols?: string[];
  leader_names: string[];
  stock_is_leader: boolean;
};

export type StockAnalysis = {
  identity: {
    symbol: string;
    name: string;
    industry: string;
  };
  review_brief: {
    review_state: string;
    headline: string;
    evidence_metrics: { label: string; value: string; note: string }[];
    risk_notes: string[];
    next_actions: string[];
  };
  data_quality: {
    ok: boolean;
    flags: string[];
  };
  data_availability: StockDataAvailability;
  event_timeline: StockEventTimelineItem[];
  sector_position: StockSectorPosition;
  limit_up_events: Record<string, string | number | boolean | null>[];
  limit_up_reviews: Record<string, string | number | boolean | null>[];
  sector_echelon: Record<string, string | number | boolean | null>[];
  strategy: StrategyDetail;
  dragon_tiger: Record<string, string | number | boolean | null>[];
  review_checklist: string[];
  safety: {
    analysis_only: boolean;
    forbidden_outputs: string[];
  };
};

export type StockAnalysisResponse = {
  analysis: StockAnalysis;
};
