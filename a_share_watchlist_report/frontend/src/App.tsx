import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, CircleDot, Database, Layers, Search, Table2, X } from "lucide-react";
import {
  fetchRuns,
  fetchSecurityDetail,
  fetchSectorWorkbench,
  fetchStockAnalysis,
  fetchStrategyCandidates,
  fetchStrategyDetail,
  fetchStrategyRuns,
  fetchSummary,
  fetchTable,
  refreshReport
} from "./api";
import { DataTable } from "./components/DataTable";
import { MetricStrip } from "./components/MetricStrip";
import { RunToolbar } from "./components/RunToolbar";
import { StatusBadge } from "./components/StatusBadge";
import type {
  ReportRun,
  ReportSummary,
  ReportTable,
  SecurityDetail,
  SectorWorkbench,
  StockAnalysis,
  StrategyCandidates,
  StrategyDetail,
  StrategyRun
} from "./types";

const sections = [
  { key: "market_regime", label: "市场状态" },
  { key: "watchlist", label: "观察池" },
  { key: "excluded_stocks", label: "排除股票" },
  { key: "holding_risk", label: "持仓风险" },
  { key: "portfolio_review", label: "组合复核" },
  { key: "dragon_tiger", label: "龙虎榜" },
  { key: "limit_up_strategy_review", label: "涨停复核" },
  { key: "limit_up_pool", label: "涨停池" },
  { key: "operations_check", label: "运行审计" },
  { key: "artifact_catalog", label: "产物目录" }
];

const strategyModules = [
  { key: "", label: "全部" },
  { key: "limit_up", label: "涨停复核" },
  { key: "watchlist", label: "观察池" },
  { key: "holding_risk", label: "持仓风险" }
];

const strategyColumns = ["module", "symbol", "name", "score", "label", "risk_flags", "reason"];

export function App() {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [runs, setRuns] = useState<ReportRun[]>([]);
  const [strategyRuns, setStrategyRuns] = useState<StrategyRun[]>([]);
  const [strategyCandidates, setStrategyCandidates] = useState<StrategyCandidates | null>(null);
  const [sectorWorkbench, setSectorWorkbench] = useState<SectorWorkbench | null>(null);
  const [strategyModule, setStrategyModule] = useState("");
  const [strategyDetail, setStrategyDetail] = useState<StrategyDetail | null>(null);
  const [tables, setTables] = useState<Record<string, ReportTable | null>>({});
  const [activeTable, setActiveTable] = useState("watchlist");
  const [searchText, setSearchText] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);
  const [securityDetail, setSecurityDetail] = useState<SecurityDetail | null>(null);
  const [stockAnalysis, setStockAnalysis] = useState<StockAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pageSize = 50;

  async function loadWorkbench() {
    setError("");
    try {
      const [nextSummary, nextRuns, tableEntries] = await Promise.all([
        fetchSummary(),
        fetchRuns(),
        Promise.all(
          sections.map((section) =>
            fetchTable(section.key, { limit: section.key === activeTable ? pageSize : 1 }).then((table) => [
              section.key,
              table
            ] as const)
          )
        )
      ]);
      const [nextStrategyRuns, nextStrategyCandidates, nextSectorWorkbench] = await Promise.all([
        fetchStrategyRuns(),
        fetchStrategyCandidates({ limit: pageSize, module: strategyModule, sortBy: "score", sortDir: "desc" }),
        fetchSectorWorkbench()
      ]);
      setSummary(nextSummary);
      setRuns(nextRuns.runs);
      setStrategyRuns(nextStrategyRuns.runs);
      setStrategyCandidates(nextStrategyCandidates);
      setSectorWorkbench(nextSectorWorkbench);
      setTables(Object.fromEntries(tableEntries));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "加载工作台失败");
    }
  }

  useEffect(() => {
    void loadWorkbench();
  }, []);

  useEffect(() => {
    setPage(0);
    setSearchText("");
    setSortBy("");
    setSecurityDetail(null);
  }, [activeTable]);

  useEffect(() => {
    async function loadActiveTable() {
      try {
        const table = await fetchTable(activeTable, {
          limit: pageSize,
          offset: page * pageSize,
          search: searchText,
          sortBy,
          sortDir
        });
        setTables((current) => ({ ...current, [activeTable]: table }));
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : "加载表格失败");
      }
    }
    void loadActiveTable();
  }, [activeTable, page, searchText, sortBy, sortDir]);

  useEffect(() => {
    async function loadStrategyCandidates() {
      try {
        setStrategyCandidates(
          await fetchStrategyCandidates({
            limit: pageSize,
            module: strategyModule,
            sortBy: "score",
            sortDir: "desc"
          })
        );
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : "加载策略候选失败");
      }
    }
    void loadStrategyCandidates();
  }, [strategyModule]);

  async function handleRefresh() {
    setBusy(true);
    setError("");
    try {
      const result = await refreshReport();
      setSummary(result.summary);
      await loadWorkbench();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "刷新报告失败");
    } finally {
      setBusy(false);
    }
  }

  const qualityTone = summary?.data_quality.ok ? "ok" : "bad";
  const qualityLabel = summary === null ? "加载中" : summary.data_quality.ok ? "OK" : "DATA_ISSUE";
  const active = useMemo(() => sections.find((section) => section.key === activeTable) ?? sections[0], [activeTable]);
  const latestRun = runs[0];
  const latestStrategyRun = strategyRuns[0];
  const activeData = tables[active.key] ?? null;
  const filteredCount = activeData?.filtered_count ?? activeData?.row_count ?? 0;
  const pageCount = Math.max(1, Math.ceil(filteredCount / pageSize));
  const strategyTable: ReportTable | null = strategyCandidates
    ? {
        name: "strategy_candidates",
        exists: true,
        columns: strategyColumns,
        row_count: strategyCandidates.row_count,
        filtered_count: strategyCandidates.filtered_count,
        limit: strategyCandidates.limit,
        offset: strategyCandidates.offset,
        rows: strategyCandidates.rows.map((row) => ({
          module: row.module,
          symbol: row.symbol,
          name: row.name,
          score: row.score,
          label: row.label,
          risk_flags: row.risk_flags,
          reason: row.reason,
        })),
        errors: [],
      }
    : null;

  function handleSort(column: string) {
    if (sortBy === column) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(column);
      setSortDir("desc");
    }
    setPage(0);
  }

  async function handleSelectSymbol(symbol: string) {
    setError("");
    try {
      setStockAnalysis(null);
      setStrategyDetail(null);
      setSecurityDetail(await fetchSecurityDetail(symbol));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "加载个股证据失败");
    }
  }

  async function handleSelectStrategySymbol(symbol: string) {
    setError("");
    try {
      setStockAnalysis(null);
      setSecurityDetail(null);
      setStrategyDetail(await fetchStrategyDetail(symbol));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "加载策略证据失败");
    }
  }

  async function handleSelectSectorStock(symbol: string) {
    setError("");
    try {
      setSecurityDetail(null);
      setStrategyDetail(null);
      setStockAnalysis((await fetchStockAnalysis(symbol)).analysis);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "加载个股复盘失败");
    }
  }

  return (
    <main className="workbench-shell">
      <aside className="review-rail" aria-label="复核模块">
        <div className="rail-mark">
          <CircleDot size={18} />
          <span>每日复盘</span>
        </div>
        <nav>
          {sections.map((section) => (
            <button
              type="button"
              key={section.key}
              className={activeTable === section.key ? "rail-item rail-item--active" : "rail-item"}
              onClick={() => setActiveTable(section.key)}
            >
              <span>{section.label}</span>
              <strong>{tables[section.key]?.row_count ?? 0}</strong>
            </button>
          ))}
        </nav>
      </aside>

      <section className="main-panel">
        <header className="top-bar">
          <div>
            <p className="eyebrow">本地投研工作台</p>
            <h1>A 股观察工作台</h1>
          </div>
          <RunToolbar busy={busy} onRefresh={handleRefresh} />
        </header>

        {error ? (
          <div className="notice notice--bad">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        ) : null}

        <section className="context-grid" aria-label="运行上下文">
          <div className="context-card">
            <div className="context-title">
              <Database size={16} />
              <span>运行上下文</span>
            </div>
            <p>{latestRun ? `${latestRun.status} · ${latestRun.message ?? "已记录"}` : "暂无运行记录"}</p>
          </div>
          <div className="context-card">
            <div className="context-title">
              {summary?.data_quality.ok ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
              <span>数据质量</span>
            </div>
            <StatusBadge label={qualityLabel} tone={qualityTone} />
          </div>
        </section>

        <MetricStrip summary={summary} />

        <section className="data-contract-panel" aria-label="数据链路契约">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">开源工程借鉴</p>
              <h2>数据链路契约</h2>
            </div>
            <div className="panel-count">
              <Database size={16} />
              <span>AKShare / EastMoney</span>
            </div>
          </div>
          <div className="data-contract-body">
            <div className="data-contract-state">
              <span>数据源状态</span>
              <strong>{sourceStateLabel(summary?.run_metrics?.data_source_state)}</strong>
              <em>来源、缓存和质量缺口必须先展示，再进入策略复核。</em>
            </div>
            <div className="data-contract-flow" aria-label="数据处理阶段">
              {["数据获取", "规格化", "质量检查", "策略复核", "人工复盘"].map((step) => (
                <span key={step}>{step}</span>
              ))}
            </div>
            <div className="data-contract-metrics">
              <div>
                <span>涨停复核</span>
                <strong>{metricText(summary?.run_metrics?.limit_up_review_count)}</strong>
              </div>
              <div>
                <span>排除股票</span>
                <strong>{metricText(summary?.run_metrics?.excluded_count)}</strong>
              </div>
              <div>
                <span>警告数</span>
                <strong>{metricText(summary?.run_metrics?.warning_count)}</strong>
              </div>
              <div>
                <span>产物数</span>
                <strong>{metricText(summary?.run_metrics?.artifact_file_count)}</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="sector-workbench" aria-label="题材梯队工作台">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">题材优先</p>
              <h2>题材梯队工作台</h2>
            </div>
            <div className="panel-count">
              <Layers size={16} />
              <span>{sectorWorkbench?.latest_trade_date || "暂无交易日"}</span>
            </div>
          </div>
          <div className="sector-summary">
            <div>
              <span>题材数</span>
              <strong>{sectorWorkbench?.summary.sector_count ?? 0}</strong>
            </div>
            <div>
              <span>涨停数</span>
              <strong>{sectorWorkbench?.summary.limit_up_count ?? 0}</strong>
            </div>
            <div>
              <span>炸板题材</span>
              <strong>{sectorWorkbench?.summary.broken_count ?? 0}</strong>
            </div>
            <div>
              <span>高标题材</span>
              <strong>{sectorWorkbench?.summary.high_board_count ?? 0}</strong>
            </div>
          </div>
          {sectorWorkbench?.errors.length ? (
            <div className="empty-state">{sectorWorkbench.errors.join("；")}</div>
          ) : null}
          <div className="sector-grid">
            {(sectorWorkbench?.cards ?? []).slice(0, 8).map((card) => (
              <article key={`${card.trade_date}-${card.industry}`} className="sector-card">
                <div className="sector-card__head">
                  <div>
                    <p className="eyebrow">板块梯队</p>
                    <h3>{card.industry}</h3>
                  </div>
                  <strong>{card.max_streak_count} 连板</strong>
                </div>
                <p className="sector-card__summary">{card.echelon_summary}</p>
                <div className="ladder-strip" aria-label={`${card.industry} 梯队`}>
                  <div>
                    <span>首板</span>
                    <strong>{card.first_board_count}</strong>
                  </div>
                  <div>
                    <span>二板</span>
                    <strong>{card.second_board_count}</strong>
                  </div>
                  <div>
                    <span>高标</span>
                    <strong>{card.high_board_count}</strong>
                  </div>
                  <div>
                    <span>炸板</span>
                    <strong>{card.broken_count}</strong>
                  </div>
                </div>
                <div className="sector-leaders" aria-label={`${card.industry} 代表股`}>
                  {card.leaders.map((leader) => (
                    <button type="button" key={leader.symbol} onClick={() => handleSelectSectorStock(leader.symbol)}>
                      <span>{leader.name}</span>
                      <strong>{leader.symbol}</strong>
                    </button>
                  ))}
                </div>
                <div className="sector-foot">
                  <span>成交额 {formatAmount(card.total_amount)}</span>
                  <div>
                    {card.risk_flags.map((flag) => (
                      <em key={flag}>{flag}</em>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="strategy-panel" aria-label="策略复核台">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">策略复核台</p>
              <h2>统一候选池</h2>
            </div>
            <div className="panel-count">
              <Table2 size={16} />
              <span>
                {strategyCandidates?.filtered_count ?? 0} / {strategyCandidates?.row_count ?? 0} 个候选
              </span>
            </div>
          </div>
          <div className="strategy-summary">
            <div>
              <span>最新策略运行</span>
              <strong>
                {latestStrategyRun
                  ? `${latestStrategyRun.status} · ${latestStrategyRun.strategy_name}`
                  : "暂无策略运行"}
              </strong>
            </div>
            <div>
              <span>候选 / 风险</span>
              <strong>
                {latestStrategyRun?.metrics.candidate_count ?? 0} / {latestStrategyRun?.metrics.risk_count ?? 0}
              </strong>
            </div>
          </div>
          <div className="strategy-tabs" aria-label="策略模块筛选">
            {strategyModules.map((module) => (
              <button
                type="button"
                key={module.key}
                className={strategyModule === module.key ? "strategy-tab strategy-tab--active" : "strategy-tab"}
                onClick={() => {
                  setStrategyModule(module.key);
                  setStrategyDetail(null);
                }}
              >
                {module.label}
              </button>
            ))}
          </div>
          <DataTable table={strategyTable} onSelectSymbol={handleSelectStrategySymbol} sortBy="score" sortDir="desc" />
        </section>

        <section className="table-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">复核队列</p>
              <h2>{active.label}</h2>
            </div>
            <div className="panel-count">
              <Table2 size={16} />
              <span>{filteredCount} / {activeData?.row_count ?? 0} 行</span>
            </div>
          </div>
          <div className="table-controls">
            <label className="search-box">
              <Search size={15} />
              <input
                value={searchText}
                onChange={(event) => {
                  setSearchText(event.target.value);
                  setPage(0);
                }}
                placeholder="按代码、名称、标签、原因筛选"
              />
            </label>
            <div className="pager">
              <button type="button" onClick={() => setPage((current) => Math.max(0, current - 1))} disabled={page === 0}>
                上一页
              </button>
              <span>{page + 1} / {pageCount}</span>
              <button
                type="button"
                onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
                disabled={page + 1 >= pageCount}
              >
                下一页
              </button>
            </div>
          </div>
          <DataTable
            table={activeData}
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={handleSort}
            onSelectSymbol={handleSelectSymbol}
          />
        </section>
      </section>

      {securityDetail ? (
        <aside className="detail-panel" aria-label="个股证据">
          <button type="button" className="detail-close" onClick={() => setSecurityDetail(null)} aria-label="关闭个股证据">
            <X size={16} />
          </button>
          <p className="eyebrow">个股证据</p>
          <h2>{securityDetail.symbol} {securityDetail.name}</h2>
          <div className="detail-score">
            <span>{securityDetail.latest_review_label || "暂无复核标签"}</span>
            <strong>{securityDetail.latest_review_score || "-"}</strong>
          </div>
          <p className="detail-flags">{securityDetail.risk_flags || "未记录风险标签"}</p>
          {Object.entries(securityDetail.sections).map(([name, rows]) => (
            <section key={name} className="detail-section">
              <h3>{sections.find((section) => section.key === name)?.label ?? name}</h3>
              {rows.slice(0, 5).map((row, index) => (
                <pre key={index}>{JSON.stringify(row, null, 2)}</pre>
              ))}
            </section>
          ))}
        </aside>
      ) : null}

      {stockAnalysis ? (
        <aside className="detail-panel stock-review-panel" aria-label="个股复盘">
          <button type="button" className="detail-close" onClick={() => setStockAnalysis(null)} aria-label="关闭个股复盘">
            <X size={16} />
          </button>
          <p className="eyebrow">个股复盘</p>
          <h2>{stockAnalysis.identity.symbol} {stockAnalysis.identity.name}</h2>
          <section className="review-brief" aria-label="复盘结论">
            <div>
              <p className="eyebrow">复盘结论</p>
              <strong>{stockAnalysis.review_brief.review_state}</strong>
            </div>
            <p>{stockAnalysis.review_brief.headline}</p>
          </section>
          <div className="detail-score">
            <span>{stockAnalysis.identity.industry}</span>
            <strong>{stockAnalysis.limit_up_reviews[0]?.review_score ?? "-"}</strong>
          </div>
          <p className="detail-flags">
            <strong>{stockAnalysis.data_quality.ok ? "数据质量正常" : "数据质量待复核"}</strong>
            {stockAnalysis.data_quality.flags.length ? <span>{stockAnalysis.data_quality.flags.join("，")}</span> : null}
          </p>
          <section className="detail-section">
            <h3>数据覆盖</h3>
            <div className="data-coverage">
              <div>
                <span>价格历史</span>
                <strong>{stockAnalysis.data_availability.price_history_available ? "已覆盖" : "缺失"}</strong>
              </div>
              <div>
                <span>涨停事件</span>
                <strong>{stockAnalysis.data_availability.limit_up_event_count}</strong>
              </div>
              <div>
                <span>板块样本</span>
                <strong>{stockAnalysis.data_availability.sector_event_count}</strong>
              </div>
              <div>
                <span>策略候选</span>
                <strong>{stockAnalysis.data_availability.strategy_candidate_count}</strong>
              </div>
              <div>
                <span>复核记录</span>
                <strong>{stockAnalysis.data_availability.review_record_count}</strong>
              </div>
              <div>
                <span>龙虎榜记录</span>
                <strong>{stockAnalysis.data_availability.dragon_tiger_count}</strong>
              </div>
            </div>
            {stockAnalysis.data_availability.missing_notes.length ? (
              <ul className="review-list review-list--risk">
                {stockAnalysis.data_availability.missing_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : null}
          </section>
          <section className="detail-section">
            <h3>关键证据</h3>
            <div className="brief-metrics">
              {stockAnalysis.review_brief.evidence_metrics.map((metric) => (
                <div key={`${metric.label}-${metric.value}`}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                  <em>{metric.note || "已记录"}</em>
                </div>
              ))}
            </div>
          </section>
          <section className="detail-section">
            <h3>风险说明</h3>
            <ul className="review-list review-list--risk">
              {stockAnalysis.review_brief.risk_notes.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <section className="detail-section">
            <h3>涨停时间线</h3>
            {stockAnalysis.event_timeline.length ? (
              <div className="event-timeline">
                {stockAnalysis.event_timeline.slice(0, 6).map((event) => (
                  <article key={`${event.trade_date}-${event.first_limit_time}`}>
                    <div className="event-timeline__head">
                      <strong>{event.trade_date}</strong>
                      <span>{event.event_profile}</span>
                    </div>
                    <dl>
                      <div>
                        <dt>首封</dt>
                        <dd>{event.first_limit_time}</dd>
                      </div>
                      <div>
                        <dt>末封</dt>
                        <dd>{event.last_limit_time}</dd>
                      </div>
                      <div>
                        <dt>炸板</dt>
                        <dd>{event.break_count} 次</dd>
                      </div>
                      <div>
                        <dt>连板</dt>
                        <dd>{event.streak_count}</dd>
                      </div>
                      <div>
                        <dt>成交额</dt>
                        <dd>{event.amount_text}</dd>
                      </div>
                      <div>
                        <dt>封单额</dt>
                        <dd>{event.seal_amount_text}</dd>
                      </div>
                      <div>
                        <dt>换手</dt>
                        <dd>{event.turnover_rate_text}</dd>
                      </div>
                      <div>
                        <dt>较上次</dt>
                        <dd>{event.close_change_from_previous_event_text}</dd>
                      </div>
                    </dl>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted-copy">暂无该股涨停时间线。</p>
            )}
          </section>
          <section className="detail-section">
            <h3>最新涨停事件</h3>
            <dl className="detail-facts">
              <div>
                <dt>交易日期</dt>
                <dd>{valueText(stockAnalysis.limit_up_events[0]?.trade_date)}</dd>
              </div>
              <div>
                <dt>连板</dt>
                <dd>{valueText(stockAnalysis.limit_up_events[0]?.streak_count)}</dd>
              </div>
              <div>
                <dt>炸板</dt>
                <dd>{valueText(stockAnalysis.limit_up_events[0]?.break_count)}</dd>
              </div>
              <div>
                <dt>成交额</dt>
                <dd>{formatAmount(Number(stockAnalysis.limit_up_events[0]?.amount ?? 0))}</dd>
              </div>
            </dl>
          </section>
          <section className="detail-section">
            <h3>所在题材梯队</h3>
            <p>{stockAnalysis.sector_position.position_summary || valueText(stockAnalysis.sector_echelon[0]?.echelon_summary)}</p>
            <div className="sector-position-grid">
              <div>
                <span>梯队位置</span>
                <strong>{stockAnalysis.sector_position.stock_is_leader ? "板块代表股" : "板块跟随股"}</strong>
              </div>
              <div>
                <span>炸板占比</span>
                <strong>{stockAnalysis.sector_position.broken_ratio_pct}%</strong>
              </div>
            </div>
            {stockAnalysis.sector_position.leader_names.length ? (
              <p className="muted-copy">代表股：{stockAnalysis.sector_position.leader_names.join("，")}</p>
            ) : null}
          </section>
          <section className="detail-section">
            <h3>历史策略复核明细</h3>
            <p className="muted-copy">复核分用于排序和排查，不代表买卖评级。每条记录对应一次历史涨停事件。</p>
            <div className="strategy-detail-list">
              {(stockAnalysis.strategy.candidates ?? []).slice(0, 6).map((candidate) => (
                <article key={candidate.id} className="strategy-detail-card">
                  <div className="strategy-detail-card__head">
                    <div>
                      <span>{valueText(candidate.source_row.trade_date)} · {candidate.module}</span>
                      <strong>涨停复核：{candidate.label}</strong>
                    </div>
                    <b>{candidate.score}</b>
                  </div>
                  <p>{candidate.reason || valueText(candidate.source_row.reason)}</p>
                  <div className="strategy-factor-grid">
                    {strategyFactors(candidate.source_row).map((factor) => (
                      <div key={`${candidate.id}-${factor.label}`}>
                        <span>{factor.label}</span>
                        <strong>{factor.value}</strong>
                      </div>
                    ))}
                  </div>
                  {candidate.source_row.score_explain ? (
                    <p className="strategy-explain">{valueText(candidate.source_row.score_explain)}</p>
                  ) : null}
                  <p className="strategy-hard-flags">
                    硬风险：{valueText(candidate.source_row.hard_flags) === "-" ? "未触发" : valueText(candidate.source_row.hard_flags)}
                  </p>
                  <p className="detail-flags">
                    <strong>风险标签</strong>
                    <span>{candidate.risk_flags || valueText(candidate.source_row.red_flags) || "未触发"}</span>
                  </p>
                </article>
              ))}
            </div>
          </section>
          <section className="detail-section">
            <h3>下一步复核</h3>
            <ul className="review-list">
              {stockAnalysis.review_brief.next_actions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <section className="detail-section">
            <h3>原始复核清单</h3>
            <ul className="review-list">
              {stockAnalysis.review_checklist.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </aside>
      ) : null}

      {strategyDetail ? (
        <aside className="detail-panel" aria-label="策略证据">
          <button type="button" className="detail-close" onClick={() => setStrategyDetail(null)} aria-label="关闭策略证据">
            <X size={16} />
          </button>
          <p className="eyebrow">策略证据</p>
          <h2>{strategyDetail.symbol}</h2>
          {(strategyDetail.candidates ?? []).map((candidate) => (
            <section key={candidate.id} className="detail-section">
              <h3>{candidate.module} · {candidate.label}</h3>
              <p>{candidate.reason}</p>
              <div className="detail-score">
                <span>复核分</span>
                <strong>{candidate.score}</strong>
              </div>
              <p className="detail-flags">{candidate.risk_flags || "未记录风险标签"}</p>
            </section>
          ))}
          {(strategyDetail.evidence ?? []).map((evidence) => (
            <section key={evidence.id} className="detail-section">
              <h3>{evidence.title}</h3>
              <p>{evidence.detail}</p>
            </section>
          ))}
        </aside>
      ) : null}
    </main>
  );
}

function formatAmount(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return "-";
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(2)} 亿`;
  if (value >= 10_000) return `${(value / 10_000).toFixed(2)} 万`;
  return String(value);
}

function valueText(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function metricText(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function sourceStateLabel(value: string | number | boolean | null | undefined): string {
  if (value === "CACHE_FALLBACK") return "本地缓存降级";
  if (value === "LIVE_OK") return "实时接口正常";
  if (value === "DATA_ISSUE") return "数据质量待复核";
  return valueText(value);
}

function strategyFactors(row: Record<string, string | number | boolean | null>): { label: string; value: string }[] {
  return [
    { label: "数据可信度", value: scoreText(row.data_confidence_score, 20) },
    { label: "板面质量", value: scoreText(row.board_quality_score, 35) },
    { label: "题材地位", value: scoreText(row.theme_position_score, 25) },
    { label: "风险惩罚", value: scoreText(row.risk_penalty_score, 60) },
    { label: "市场环境", value: valueText(row.market_context) },
    { label: "涨停强度", value: valueText(row.limit_up_strength) },
    { label: "连板分", value: valueText(row.streak_score) },
    { label: "封板质量", value: valueText(row.board_quality) },
    { label: "流动性", value: valueText(row.liquidity_score) },
    { label: "隔夜风险", value: valueText(row.overnight_risk) },
    { label: "数据质量", value: valueText(row.data_quality_score) }
  ].filter((factor) => factor.value !== "-");
}

function scoreText(value: string | number | boolean | null | undefined, maxScore: number): string {
  if (value === null || value === undefined || value === "") return "-";
  return `${value}/${maxScore}`;
}
