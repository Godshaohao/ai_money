import type { ReportTable } from "../types";

type DataTableProps = {
  table: ReportTable | null;
};

const columnLabels: Record<string, string> = {
  above_ma200: "高于 MA200",
  artifact_name: "产物",
  amount: "成交额",
  avg_amount_20d: "20 日平均成交额",
  board_quality: "封板质量",
  break_count: "炸板次数",
  buy_amount: "买入额",
  change_pct: "涨跌幅",
  check_name: "检查项",
  close: "收盘价",
  cost_basis: "成本价",
  cost_value: "成本市值",
  data_quality_score: "数据质量分",
  deal_amount: "成交额",
  detail: "说明",
  drawdown_from_cost: "成本回撤",
  exclude_reason: "排除原因",
  first_limit_time: "首次封板时间",
  filename: "文件",
  holding_risk: "持仓风险",
  industry: "行业",
  index_code: "指数代码",
  index_name: "指数名称",
  last_price_date: "最新价格日期",
  last_limit_time: "最后封板时间",
  latest_close: "最新价",
  liquidity_days: "流动性天数",
  liquidity_score: "流动性分",
  limit_up_stats: "涨停统计",
  limit_up_strength: "涨停强度",
  market_context: "市场环境",
  max_drawdown_60d: "60 日最大回撤",
  momentum_12m: "12M 动量",
  momentum_6m: "6M 动量",
  name: "名称",
  net_buy_amount: "净买入额",
  overnight_risk: "隔夜风险",
  portfolio_weight: "组合权重",
  position_value: "持仓市值",
  rank: "排名",
  reason: "原因",
  red_flags: "风险标签",
  return_20d: "20D 收益",
  review_label: "复核标签",
  review_note: "复核说明",
  review_score: "复核分",
  risk_action: "风险动作",
  risk_flags: "风险标签",
  sell_amount: "卖出额",
  severity: "级别",
  seal_amount: "封板资金",
  shares: "持仓数量",
  source: "来源",
  status: "状态",
  streak_count: "连板数",
  streak_score: "连板分",
  symbol: "代码",
  trade_date: "交易日期",
  turnover_rate: "换手率",
  unrealized_pnl: "浮动盈亏",
  unrealized_return: "浮动收益率",
  updated_at: "更新时间",
};

export function DataTable({ table }: DataTableProps) {
  if (table === null) {
    return <div className="empty-state">正在加载表格</div>;
  }

  if (!table.exists) {
    return <div className="empty-state">{table.errors[0] ?? "暂无表格数据"}</div>;
  }

  if (table.columns.length === 0) {
    return <div className="empty-state">暂无行数据</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {table.columns.map((column) => (
              <th key={column}>{columnLabels[column] ?? column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {table.columns.map((column) => (
                <td key={column}>{String(row[column] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
