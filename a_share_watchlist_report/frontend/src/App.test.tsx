import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { App } from "./App";

const summary = {
  exists: true,
  missing_files: [],
  data_quality: { ok: true, warnings: [] },
  run_metrics: {
    operations_warn_count: 1,
    operations_fail_count: 0,
    artifact_file_count: 11,
    data_source_state: "CACHE_FALLBACK",
    limit_up_review_count: 913,
    excluded_count: 97,
    warning_count: 1
  },
  row_counts: {
    watchlist: 1,
    excluded_stocks: 2,
    holding_risk: 0,
    market_regime: 1,
    operations_check: 5,
    artifact_catalog: 11
  },
  artifacts: {}
};

const watchlistTable = {
  name: "watchlist",
  exists: true,
  columns: ["symbol", "name", "reason"],
  row_count: 1,
  rows: [{ symbol: "600519", name: "贵州茅台", reason: "12M 动量 10%" }],
  errors: []
};

const securityDetail = {
  symbol: "600519",
  exists: true,
  name: "贵州茅台",
  latest_review_label: "WATCH_REVIEW",
  latest_review_score: "88",
  risk_flags: "HISTORY_GAP",
  sections: {
    watchlist: [{ symbol: "600519", name: "贵州茅台", reason: "12M 动量 10%" }]
  }
};

const strategyRuns = {
  runs: [
    {
      id: 7,
      strategy_name: "all",
      status: "SUCCESS",
      started_at: "2026-07-11T10:00:00+08:00",
      finished_at: "2026-07-11T10:01:00+08:00",
      message: "策略复核完成",
      params: { modules: ["limit_up", "watchlist", "holding_risk"] },
      metrics: { candidate_count: 2, risk_count: 1 }
    }
  ]
};

const strategyCandidates = {
  run_id: 7,
  row_count: 2,
  filtered_count: 2,
  limit: 50,
  offset: 0,
  rows: [
    {
      id: 1,
      run_id: 7,
      module: "watchlist",
      symbol: "600519",
      name: "贵州茅台",
      score: 100,
      label: "CORE_REVIEW",
      risk_flags: "",
      reason: "观察池复核",
      source_table: "watchlist",
      source_row: { rank: 1 }
    },
    {
      id: 2,
      run_id: 7,
      module: "holding_risk",
      symbol: "300750",
      name: "宁德时代",
      score: 40,
      label: "RISK_REVIEW",
      risk_flags: "BELOW_MA200",
      reason: "持仓风险复核",
      source_table: "holding_risk",
      source_row: { above_ma200: false }
    }
  ]
};

const strategyDetail = {
  symbol: "300750",
  exists: true,
  candidates: [strategyCandidates.rows[1]],
  evidence: [
    {
      id: 1,
      run_id: 7,
      symbol: "300750",
      module: "holding_risk",
      evidence_type: "holding_risk",
      title: "持仓风险证据",
      detail: "持仓风险复核；风险标签 BELOW_MA200",
      payload: { above_ma200: false }
    }
  ]
};

const menoStrategyDetail = {
  symbol: "603538",
  exists: true,
  candidates: [
    {
      id: 3,
      run_id: 7,
      module: "limit_up",
      symbol: "603538",
      name: "美诺华",
      score: 48,
      label: "DATA_REVIEW",
      risk_flags: "HISTORY_GAP,BROKEN_BOARD_RISK",
      reason: "近期涨停复核：涨幅 10.01%，连板 1，炸板 9，成交额 21.35 亿；风险标签 HISTORY_GAP,BROKEN_BOARD_RISK",
      source_table: "limit_up_strategy_review",
      source_row: {
        trade_date: "2026-07-10",
        market_context: "SUPPORTIVE",
        data_confidence_score: 10,
        board_quality_score: 14,
        theme_position_score: 14,
        risk_penalty_score: 42,
        hard_flags: "HISTORY_GAP,BROKEN_BOARD_RISK",
        limit_up_strength: 20,
        streak_score: 5,
        board_quality: 4,
        liquidity_score: 10,
        overnight_risk: 3,
        data_quality_score: 7,
        review_score: 48,
        review_label: "DATA_REVIEW",
        red_flags: "HISTORY_GAP,BROKEN_BOARD_RISK",
        score_explain: "数据可信度 10/20；板面质量 14/35；题材地位 14/25；风险惩罚 42/60；硬风险 HISTORY_GAP,BROKEN_BOARD_RISK",
        reason: "近期涨停复核：涨幅 10.01%，连板 1，炸板 9，成交额 21.35 亿；风险标签 HISTORY_GAP,BROKEN_BOARD_RISK"
      }
    }
  ],
  evidence: []
};

const sectorWorkbench = {
  latest_trade_date: "2026-07-10",
  summary: {
    sector_count: 2,
    limit_up_count: 3,
    broken_count: 1,
    high_board_count: 0
  },
  cards: [
    {
      trade_date: "2026-07-10",
      industry: "化学制药",
      limit_up_count: 2,
      first_board_count: 1,
      second_board_count: 1,
      high_board_count: 0,
      max_streak_count: 2,
      broken_count: 1,
      total_amount: 2934658736,
      leader_symbols: ["600276", "603538"],
      leader_names: ["恒瑞医药", "美诺华"],
      leaders: [
        { symbol: "600276", name: "恒瑞医药" },
        { symbol: "603538", name: "美诺华" }
      ],
      echelon_summary: "涨停 2；首板 1；二板 1；高标 0；最高 2 连板；炸板 1",
      risk_flags: ["炸板 1", "无高标"]
    }
  ],
  errors: []
};

const stockAnalysis = {
  analysis: {
    identity: { symbol: "603538", name: "美诺华", industry: "化学制药" },
    review_brief: {
      review_state: "风险优先复核",
      headline: "美诺华 属于 化学制药，最新涨停为 1 连板、炸板 9 次，首封 10:07:58，末封 13:26:58，封单 5593.85 万，成交额 21.35 亿，但存在数据质量缺口，应先做复核而非直接下结论。",
      evidence_metrics: [
        { label: "最新板位", value: "1 连板", note: "2026-07-10" },
        { label: "炸板情况", value: "炸板 9 次", note: "回封稳定性是主要复核点" },
        { label: "板块梯队", value: "涨停 2；首板 1；二板 1；高标 0；最高 2 连板；炸板 1", note: "2026-07-10" }
      ],
      risk_notes: [
        "最新涨停炸板 9 次，说明盘中分歧较大，需要复核回封时间和封单变化。",
        "较上一条涨停收盘变化 -21.60%，需要复核连板断裂后的承接情况。",
        "所属板块炸板占比 50%，代表股包括 恒瑞医药，美诺华。"
      ],
      next_actions: ["复核最新涨停的炸板原因、回封时间、封单金额和成交额变化。"]
    },
    data_quality: { ok: false, flags: ["no price data", "HISTORY_GAP"] },
    data_availability: {
      price_history_available: false,
      limit_up_event_count: 2,
      sector_event_count: 2,
      strategy_candidate_count: 1,
      review_record_count: 1,
      dragon_tiger_count: 0,
      missing_notes: ["价格历史缺失，无法计算 MA、动量、回撤。"]
    },
    event_timeline: [
      {
        trade_date: "2026-07-10",
        event_profile: "分歧回封",
        streak_count: 1,
        break_count: 9,
        first_limit_time: "10:07:58",
        last_limit_time: "13:26:58",
        close: 30.88,
        change_pct: 10.01,
        change_pct_text: "10.01%",
        turnover_rate: 21.23,
        turnover_rate_text: "21.23%",
        amount: 2134658736,
        amount_text: "21.35 亿",
        seal_amount: 55938471,
        seal_amount_text: "5593.85 万",
        limit_up_stats: "1/1",
        close_change_from_previous_event_pct: -21.6,
        close_change_from_previous_event_text: "-21.60%"
      },
      {
        trade_date: "2026-07-09",
        event_profile: "温和分歧",
        streak_count: 1,
        break_count: 2,
        first_limit_time: "10:30:00",
        last_limit_time: "14:30:00",
        close: 39.39,
        change_pct: 10.01,
        change_pct_text: "10.01%",
        turnover_rate: 18.23,
        turnover_rate_text: "18.23%",
        amount: 1500000000,
        amount_text: "15.00 亿",
        seal_amount: 30000000,
        seal_amount_text: "3000.00 万",
        limit_up_stats: "1/1",
        close_change_from_previous_event_pct: null,
        close_change_from_previous_event_text: "无上一条记录"
      }
    ],
    sector_position: {
      trade_date: "2026-07-10",
      industry: "化学制药",
      position_summary: "化学制药 当日涨停 2 只，炸板 1 只，最高 2 连板。",
      limit_up_count: 2,
      first_board_count: 1,
      second_board_count: 1,
      high_board_count: 0,
      max_streak_count: 2,
      broken_count: 1,
      broken_ratio_pct: 50,
      leader_symbols: ["600276", "603538"],
      leader_names: ["恒瑞医药", "美诺华"],
      stock_is_leader: true
    },
    limit_up_events: [
      {
        trade_date: "2026-07-10",
        close: 30.88,
        amount: 2134658736,
        break_count: 9,
        streak_count: 1,
        first_limit_time: "100758",
        last_limit_time: "132658"
      }
    ],
    limit_up_reviews: [
      {
        trade_date: "2026-07-10",
        review_score: 69,
        review_label: "WATCH_REVIEW",
        red_flags: "HISTORY_GAP,BROKEN_BOARD_RISK"
      }
    ],
    sector_echelon: [
      {
        trade_date: "2026-07-10",
        industry: "化学制药",
        echelon_summary: "涨停 2；首板 1；二板 1；高标 0；最高 2 连板；炸板 1"
      }
    ],
    strategy: menoStrategyDetail,
    dragon_tiger: [],
    review_checklist: ["复核涨停事件数量 1，最高炸板次数 9。", "重点复核炸板原因、回封时间和封单稳定性。"],
    safety: {
      analysis_only: true,
      forbidden_outputs: ["BUY", "SELL", "target_price", "broker_order", "automated_trading"]
    }
  }
};

const emptyTable = (name: string) => ({
  name,
  exists: true,
  columns: ["symbol"],
  row_count: 0,
  rows: [],
  errors: []
});

describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("renders the workbench shell and watchlist data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = String(input);
        const parsed = new URL(url, "http://test.local");
        if (parsed.pathname.endsWith("/summary")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(summary) });
        }
        if (parsed.pathname.endsWith("/api/report/runs")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ runs: [] }) });
        }
        if (parsed.pathname.endsWith("/api/strategy/runs")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(strategyRuns) });
        }
        if (parsed.pathname.endsWith("/api/strategy/candidates")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(strategyCandidates) });
        }
        if (parsed.pathname.endsWith("/api/strategy/securities/300750")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(strategyDetail) });
        }
        if (parsed.pathname.endsWith("/api/analysis/sectors")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(sectorWorkbench) });
        }
        if (parsed.pathname.endsWith("/api/analysis/stocks/603538")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(stockAnalysis) });
        }
        if (parsed.pathname.endsWith("/tables/watchlist")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(watchlistTable) });
        }
        if (parsed.pathname.endsWith("/securities/600519")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(securityDetail) });
        }
        const name = parsed.pathname.split("/").pop() ?? "unknown";
        return Promise.resolve({ ok: true, json: () => Promise.resolve(emptyTable(name)) });
      })
    );

    render(<App />);

    expect(screen.getByText("A 股观察工作台")).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText("600519").length).toBeGreaterThan(0));
    expect(screen.getAllByText("代码").length).toBeGreaterThan(0);
    expect(screen.getAllByText("原因").length).toBeGreaterThan(0);
    expect(screen.getByText("数据质量")).toBeInTheDocument();
    expect(screen.getByText("数据链路契约")).toBeInTheDocument();
    expect(screen.getByText("AKShare / EastMoney")).toBeInTheDocument();
    expect(screen.getByText("本地缓存降级")).toBeInTheDocument();
    expect(screen.getByText("数据获取")).toBeInTheDocument();
    expect(screen.getByText("质量检查")).toBeInTheDocument();
    expect(screen.getByText("人工复盘")).toBeInTheDocument();
    expect(screen.getAllByText("观察池").length).toBeGreaterThan(0);
    expect(screen.getByText("组合复核")).toBeInTheDocument();
    expect(screen.getByText("龙虎榜")).toBeInTheDocument();
    expect(screen.getAllByText("涨停复核").length).toBeGreaterThan(0);
    expect(screen.getByText("运行审计")).toBeInTheDocument();
    expect(screen.getByText("产物目录")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("题材梯队工作台")).toBeInTheDocument());
    expect(screen.getByText("化学制药")).toBeInTheDocument();
    expect(screen.getByText("涨停 2；首板 1；二板 1；高标 0；最高 2 连板；炸板 1")).toBeInTheDocument();
    expect(screen.getByText("炸板 1")).toBeInTheDocument();
    fireEvent.click(screen.getByText("美诺华"));
    await waitFor(() => expect(screen.getByText("个股复盘")).toBeInTheDocument());
    expect(screen.getByText("603538 美诺华")).toBeInTheDocument();
    expect(screen.getByText("复盘结论")).toBeInTheDocument();
    expect(screen.getByText("风险优先复核")).toBeInTheDocument();
    expect(screen.getByText("美诺华 属于 化学制药，最新涨停为 1 连板、炸板 9 次，首封 10:07:58，末封 13:26:58，封单 5593.85 万，成交额 21.35 亿，但存在数据质量缺口，应先做复核而非直接下结论。")).toBeInTheDocument();
    expect(screen.getByText("较上一条涨停收盘变化 -21.60%，需要复核连板断裂后的承接情况。")).toBeInTheDocument();
    expect(screen.getByText("数据质量待复核")).toBeInTheDocument();
    expect(screen.getByText("数据覆盖")).toBeInTheDocument();
    expect(screen.getByText("价格历史缺失，无法计算 MA、动量、回撤。")).toBeInTheDocument();
    expect(screen.getByText("涨停时间线")).toBeInTheDocument();
    expect(screen.getByText("分歧回封")).toBeInTheDocument();
    expect(screen.getByText("10:07:58")).toBeInTheDocument();
    expect(screen.getByText("5593.85 万")).toBeInTheDocument();
    expect(screen.getByText("板块代表股")).toBeInTheDocument();
    expect(screen.getByText("代表股：恒瑞医药，美诺华")).toBeInTheDocument();
    expect(screen.getByText("历史策略复核明细")).toBeInTheDocument();
    expect(screen.getByText("2026-07-10 · limit_up")).toBeInTheDocument();
    expect(screen.getByText("涨停复核：DATA_REVIEW")).toBeInTheDocument();
    expect(screen.getByText("数据可信度")).toBeInTheDocument();
    expect(screen.getByText("题材地位")).toBeInTheDocument();
    expect(screen.getByText("风险惩罚")).toBeInTheDocument();
    expect(screen.getByText("硬风险：HISTORY_GAP,BROKEN_BOARD_RISK")).toBeInTheDocument();
    expect(screen.getByText("数据可信度 10/20；板面质量 14/35；题材地位 14/25；风险惩罚 42/60；硬风险 HISTORY_GAP,BROKEN_BOARD_RISK")).toBeInTheDocument();
    expect(screen.getByText("HISTORY_GAP,BROKEN_BOARD_RISK")).toBeInTheDocument();
    expect(screen.getByText("近期涨停复核：涨幅 10.01%，连板 1，炸板 9，成交额 21.35 亿；风险标签 HISTORY_GAP,BROKEN_BOARD_RISK")).toBeInTheDocument();
    expect(screen.getByText("回封稳定性是主要复核点")).toBeInTheDocument();
    expect(screen.getByText("复核最新涨停的炸板原因、回封时间、封单金额和成交额变化。")).toBeInTheDocument();
    expect(screen.getByText("重点复核炸板原因、回封时间和封单稳定性。")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("策略复核台")).toBeInTheDocument());
    expect(screen.getByText("统一候选池")).toBeInTheDocument();
    expect(screen.getByText("CORE_REVIEW")).toBeInTheDocument();
    expect(screen.getByText("持仓风险复核")).toBeInTheDocument();
    expect(screen.getByText("1W/0F")).toBeInTheDocument();
    const reportSymbolCells = screen.getAllByText("600519");
    fireEvent.click(reportSymbolCells[reportSymbolCells.length - 1]);
    await waitFor(() => expect(screen.getByText("个股证据")).toBeInTheDocument());
    expect(screen.getByText("WATCH_REVIEW")).toBeInTheDocument();
    fireEvent.click(screen.getByText("300750"));
    await waitFor(() => expect(screen.getByText("策略证据")).toBeInTheDocument());
    expect(screen.getByText("持仓风险证据")).toBeInTheDocument();
  });
});
