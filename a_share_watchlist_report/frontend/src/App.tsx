import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, CircleDot, Database, Table2 } from "lucide-react";
import { fetchRuns, fetchSummary, fetchTable, refreshReport } from "./api";
import { DataTable } from "./components/DataTable";
import { MetricStrip } from "./components/MetricStrip";
import { RunToolbar } from "./components/RunToolbar";
import { StatusBadge } from "./components/StatusBadge";
import type { ReportRun, ReportSummary, ReportTable } from "./types";

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
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadWorkbench() {
    setError("");
    try {
      const [nextSummary, nextRuns, tableEntries] = await Promise.all([
        fetchSummary(),
        fetchRuns(),
        Promise.all(sections.map((section) => fetchTable(section.key).then((table) => [section.key, table] as const)))
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
              <p className="eyebrow">生成结果表</p>
              <h2>{active.label}</h2>
            </div>
            <div className="panel-count">
              <Table2 size={16} />
              <span>{tables[active.key]?.row_count ?? 0} 行</span>
            </div>
          </div>
          <DataTable table={tables[active.key] ?? null} />
        </section>
      </section>
    </main>
  );
}
