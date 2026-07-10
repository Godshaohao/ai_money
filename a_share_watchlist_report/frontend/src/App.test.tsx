import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { App } from "./App";

const summary = {
  exists: true,
  missing_files: [],
  data_quality: { ok: true, warnings: [] },
  run_metrics: {
    operations_warn_count: 1,
    operations_fail_count: 0,
    artifact_file_count: 11
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
        if (url.endsWith("/summary")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(summary) });
        }
        if (url.endsWith("/runs")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ runs: [] }) });
        }
        if (url.endsWith("/tables/watchlist")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(watchlistTable) });
        }
        const name = url.split("/").pop() ?? "unknown";
        return Promise.resolve({ ok: true, json: () => Promise.resolve(emptyTable(name)) });
      })
    );

    render(<App />);

    expect(screen.getByText("A 股观察工作台")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("600519")).toBeInTheDocument());
    expect(screen.getByText("代码")).toBeInTheDocument();
    expect(screen.getByText("原因")).toBeInTheDocument();
    expect(screen.getByText("数据质量")).toBeInTheDocument();
    expect(screen.getAllByText("观察池").length).toBeGreaterThan(0);
    expect(screen.getByText("组合复核")).toBeInTheDocument();
    expect(screen.getByText("龙虎榜")).toBeInTheDocument();
    expect(screen.getByText("涨停复核")).toBeInTheDocument();
    expect(screen.getByText("运行审计")).toBeInTheDocument();
    expect(screen.getByText("产物目录")).toBeInTheDocument();
    expect(screen.getByText("1W/0F")).toBeInTheDocument();
  });
});
