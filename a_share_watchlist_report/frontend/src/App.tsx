import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, CircleDot, Database, Search, Table2, X } from "lucide-react";
import { fetchRuns, fetchSecurityDetail, fetchSummary, fetchTable, refreshReport } from "./api";
import { DataTable } from "./components/DataTable";
import { MetricStrip } from "./components/MetricStrip";
import { RunToolbar } from "./components/RunToolbar";
import { StatusBadge } from "./components/StatusBadge";
import type { ReportRun, ReportSummary, ReportTable, SecurityDetail } from "./types";

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

export function App() {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [runs, setRuns] = useState<ReportRun[]>([]);
  const [tables, setTables] = useState<Record<string, ReportTable | null>>({});
  const [activeTable, setActiveTable] = useState("watchlist");
  const [searchText, setSearchText] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);
  const [securityDetail, setSecurityDetail] = useState<SecurityDetail | null>(null);
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
      setSummary(nextSummary);
      setRuns(nextRuns.runs);
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
  const activeData = tables[active.key] ?? null;
  const filteredCount = activeData?.filtered_count ?? activeData?.row_count ?? 0;
  const pageCount = Math.max(1, Math.ceil(filteredCount / pageSize));

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
      setSecurityDetail(await fetchSecurityDetail(symbol));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "加载个股证据失败");
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
    </main>
  );
}
