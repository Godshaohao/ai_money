import type { ReportSummary } from "../types";

type MetricStripProps = {
  summary: ReportSummary | null;
};

export function MetricStrip({ summary }: MetricStripProps) {
  const counts = summary?.row_counts ?? {};
  return (
    <section className="metric-strip" aria-label="Report metrics">
      <div>
        <span>Watchlist</span>
        <strong>{counts.watchlist ?? 0}</strong>
      </div>
      <div>
        <span>Excluded</span>
        <strong>{counts.excluded_stocks ?? 0}</strong>
      </div>
      <div>
        <span>Holding risk</span>
        <strong>{counts.holding_risk ?? 0}</strong>
      </div>
      <div>
        <span>Regime rows</span>
        <strong>{counts.market_regime ?? 0}</strong>
      </div>
    </section>
  );
}
