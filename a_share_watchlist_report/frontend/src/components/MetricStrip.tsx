import type { ReportSummary } from "../types";

type MetricStripProps = {
  summary: ReportSummary | null;
};

export function MetricStrip({ summary }: MetricStripProps) {
  const counts = summary?.row_counts ?? {};
  const metrics = summary?.run_metrics ?? {};
  return (
    <section className="metric-strip" aria-label="报告指标">
      <div>
        <span>观察池</span>
        <strong>{counts.watchlist ?? 0}</strong>
      </div>
      <div>
        <span>排除股票</span>
        <strong>{counts.excluded_stocks ?? 0}</strong>
      </div>
      <div>
        <span>持仓风险</span>
        <strong>{counts.holding_risk ?? 0}</strong>
      </div>
      <div>
        <span>市场状态</span>
        <strong>{counts.market_regime ?? 0}</strong>
      </div>
      <div>
        <span>运行检查</span>
        <strong>{String(metrics.operations_warn_count ?? 0)}W/{String(metrics.operations_fail_count ?? 0)}F</strong>
      </div>
      <div>
        <span>产物文件</span>
        <strong>{String(metrics.artifact_file_count ?? 0)}</strong>
      </div>
    </section>
  );
}
