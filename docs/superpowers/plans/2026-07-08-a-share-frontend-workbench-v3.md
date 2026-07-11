# A-share Frontend Workbench V3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local front-end research workbench that consumes the V2 FastAPI backend and presents the existing A-share report outputs as an interactive, non-trading dashboard.

**Architecture:** Keep `run_report.py` and the six P0 output files as the canonical report contract. Extend the V2 backend with read-only table APIs for generated CSV artifacts, then add a Vite + React + TypeScript frontend under `a_share_watchlist_report/frontend/`. The frontend is a local workbench shell, not a public landing page and not a trading terminal.

**Tech Stack:** Python, FastAPI, pandas, pytest, SQLite, React, Vite, TypeScript, Vitest, native CSS, lucide-react.

---

## Guardrails

- Keep `python run_report.py` working.
- Keep V2 backend endpoints working: `/health`, `/api/report/summary`, `/api/report/run`, `/api/report/runs`.
- Do not add broker APIs, account login, orders, BUY/SELL labels, target prices, ML/AI commentary, backtesting, or another market data source.
- The frontend may trigger `POST /api/report/run`, but it must label the action as refreshing a local report, not trading.
- The frontend displays existing generated data only: watchlist, excluded stocks, holding risk, market regime, dragon tiger list, and data quality.
- Use dense, utilitarian dashboard design. No hero landing page, no marketing copy, no decorative gradient blobs.
- Preserve the static HTML report output; V3 is additive.

## Design Direction

Subject: a local A-share research workbench for one personal investor doing daily review.

Visual system:
- `ink`: `#14171A`
- `paper`: `#F7F8F5`
- `line`: `#D8DDD2`
- `steel`: `#4A6473`
- `risk`: `#B4483E`
- `signal`: `#2F7D57`
- `amber`: `#B9872F`

Typography:
- Display and section labels: system sans with `font-weight: 700`.
- Table/body text: system sans with tabular numbers.
- Utility metadata: smaller uppercase labels with normal letter spacing.

Layout:

```text
┌──────────────────────────────────────────────────────────┐
│ Top bar: A-share Workbench | refresh | backend status     │
├──────────────┬───────────────────────────────────────────┤
│ Left rail    │ Run context + data quality strip           │
│ sections     ├───────────────────────────────────────────┤
│              │ Market regime | Watchlist | Risk panels    │
│              ├───────────────────────────────────────────┤
│              │ Dense data tables with sticky headers      │
└──────────────┴───────────────────────────────────────────┘
```

Signature element: a slim left “review rail” that shows the daily review sequence: Regime, Watchlist, Exclusions, Holdings, Dragon Tiger, Quality. It is navigation and status, not decoration.

## File Structure

- Modify `a_share_watchlist_report/backend/app.py`
  - Include the new table router.
- Create `a_share_watchlist_report/backend/services/tables.py`
  - Read generated CSV artifacts into JSON-safe table payloads.
- Create `a_share_watchlist_report/backend/routes/tables.py`
  - Expose `GET /api/report/tables/{table_name}`.
- Add `a_share_watchlist_report/tests/test_backend_tables.py`
  - Unit tests for table parsing and invalid table names.
- Add `a_share_watchlist_report/tests/test_backend_table_api.py`
  - ASGI contract tests for the table endpoint.
- Create `a_share_watchlist_report/frontend/package.json`
  - Vite/React scripts and dependencies.
- Create `a_share_watchlist_report/frontend/index.html`
  - Root HTML shell.
- Create `a_share_watchlist_report/frontend/tsconfig.json`
  - TypeScript config.
- Create `a_share_watchlist_report/frontend/vite.config.ts`
  - Vite config and backend proxy.
- Create `a_share_watchlist_report/frontend/src/main.tsx`
  - React entrypoint.
- Create `a_share_watchlist_report/frontend/src/App.tsx`
  - Workbench shell and data loading.
- Create `a_share_watchlist_report/frontend/src/api.ts`
  - Fetch wrappers.
- Create `a_share_watchlist_report/frontend/src/types.ts`
  - Shared frontend types.
- Create `a_share_watchlist_report/frontend/src/components/StatusBadge.tsx`
  - Status badge.
- Create `a_share_watchlist_report/frontend/src/components/DataTable.tsx`
  - Dense table component.
- Create `a_share_watchlist_report/frontend/src/components/MetricStrip.tsx`
  - Summary metric strip.
- Create `a_share_watchlist_report/frontend/src/components/RunToolbar.tsx`
  - Refresh report button and run status.
- Create `a_share_watchlist_report/frontend/src/styles.css`
  - Full application styling.
- Add `a_share_watchlist_report/frontend/src/App.test.tsx`
  - Frontend render and interaction tests.
- Modify `a_share_watchlist_report/README.md`
  - Document V3 local workbench commands.
- Modify `a_share_watchlist_report/.gitignore`
  - Ignore frontend generated artifacts.

## Task 1: Backend Table Service

**Files:**
- Create: `a_share_watchlist_report/backend/services/tables.py`
- Test: `a_share_watchlist_report/tests/test_backend_tables.py`

- [ ] **Step 1: Write failing table service tests**

```python
from pathlib import Path

import pandas as pd
import pytest

from backend.services.tables import read_report_table


def test_read_report_table_returns_rows_and_columns(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "score": 1.25},
            {"symbol": "300750", "name": "宁德时代", "score": None},
        ]
    ).to_csv(output_dir / "watchlist.csv", index=False)

    table = read_report_table(output_dir, "watchlist")

    assert table["name"] == "watchlist"
    assert table["exists"] is True
    assert table["columns"] == ["symbol", "name", "score"]
    assert table["row_count"] == 2
    assert table["rows"][0]["symbol"] == "600519"
    assert table["rows"][1]["score"] is None


def test_read_report_table_reports_missing_file(tmp_path: Path) -> None:
    table = read_report_table(tmp_path / "output", "watchlist")

    assert table["name"] == "watchlist"
    assert table["exists"] is False
    assert table["rows"] == []
    assert table["errors"]


def test_read_report_table_rejects_unknown_table(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown report table"):
        read_report_table(tmp_path / "output", "orders")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_tables.py -q`

Expected: FAIL because `backend.services.tables` does not exist.

- [ ] **Step 3: Implement table service**

Create `backend/services/tables.py`:

```python
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


REPORT_TABLES = {
    "watchlist": "watchlist.csv",
    "excluded_stocks": "excluded_stocks.csv",
    "holding_risk": "holding_risk.csv",
    "market_regime": "market_regime.csv",
    "dragon_tiger": "dragon_tiger.csv",
}


def read_report_table(output_dir: Path, table_name: str, limit: int = 200) -> dict[str, Any]:
    if table_name not in REPORT_TABLES:
        raise ValueError(f"unknown report table: {table_name}")

    path = Path(output_dir) / REPORT_TABLES[table_name]
    if not path.exists():
        return {
            "name": table_name,
            "exists": False,
            "columns": [],
            "row_count": 0,
            "rows": [],
            "errors": [f"Missing {path.name}"],
        }

    try:
        frame = pd.read_csv(path, dtype="string")
    except (EmptyDataError, ParserError, UnicodeDecodeError, OSError) as exc:
        return {
            "name": table_name,
            "exists": False,
            "columns": [],
            "row_count": 0,
            "rows": [],
            "errors": [f"Malformed {path.name}: {exc}"],
        }

    limited = frame.head(limit)
    rows = limited.where(pd.notna(limited), None).to_dict(orient="records")
    return {
        "name": table_name,
        "exists": True,
        "columns": list(frame.columns),
        "row_count": int(len(frame)),
        "rows": rows,
        "errors": [],
    }
```

- [ ] **Step 4: Run table service tests**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_tables.py -q`

Expected: PASS.

## Task 2: Backend Table API

**Files:**
- Modify: `a_share_watchlist_report/backend/app.py`
- Create: `a_share_watchlist_report/backend/routes/tables.py`
- Test: `a_share_watchlist_report/tests/test_backend_table_api.py`

- [ ] **Step 1: Write failing ASGI API tests**

```python
import asyncio
import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI

from backend.app import create_app


def _call_json(app: FastAPI, method: str, path: str) -> tuple[int, dict]:
    messages: list[dict] = []
    sent = False

    async def receive() -> dict:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("ascii"),
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return int(start["status"]), json.loads(body.decode("utf-8"))


def test_table_endpoint_returns_watchlist_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "600519", "name": "贵州茅台"}]).to_csv(output_dir / "watchlist.csv", index=False)
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")

    status_code, body = _call_json(app, "GET", "/api/report/tables/watchlist")

    assert status_code == 200
    assert body["name"] == "watchlist"
    assert body["rows"][0]["symbol"] == "600519"


def test_table_endpoint_rejects_unknown_table(tmp_path: Path) -> None:
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")

    status_code, body = _call_json(app, "GET", "/api/report/tables/orders")

    assert status_code == 404
    assert body["detail"] == "unknown report table"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_table_api.py -q`

Expected: FAIL because `/api/report/tables/{table_name}` is not registered.

- [ ] **Step 3: Implement table router**

Create `backend/routes/tables.py`:

```python
from fastapi import APIRouter, HTTPException, Request

from backend.services.tables import read_report_table


router = APIRouter(prefix="/api/report/tables")


@router.get("/{table_name}")
async def report_table(table_name: str, request: Request) -> dict:
    try:
        return read_report_table(request.app.state.output_dir, table_name)
    except ValueError:
        raise HTTPException(status_code=404, detail="unknown report table")
```

Modify `backend/app.py`:

```python
from backend.routes.tables import router as tables_router

app.include_router(tables_router)
```

- [ ] **Step 4: Run table API tests**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_table_api.py -q`

Expected: PASS.

## Task 3: Frontend Scaffold

**Files:**
- Create: `a_share_watchlist_report/frontend/package.json`
- Create: `a_share_watchlist_report/frontend/index.html`
- Create: `a_share_watchlist_report/frontend/tsconfig.json`
- Create: `a_share_watchlist_report/frontend/vite.config.ts`
- Create: `a_share_watchlist_report/frontend/src/main.tsx`
- Create: `a_share_watchlist_report/frontend/src/types.ts`
- Create: `a_share_watchlist_report/frontend/src/api.ts`
- Modify: `a_share_watchlist_report/.gitignore`

- [ ] **Step 1: Create frontend package**

Create `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^6.0.0",
    "typescript": "^5.7.2",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.3",
    "@types/react": "^19.0.1",
    "@types/react-dom": "^19.0.2",
    "jsdom": "^25.0.1",
    "vitest": "^2.1.8"
  }
}
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>A-share Workbench</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

Create `frontend/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000"
    }
  },
  test: {
    environment: "jsdom",
    globals: true
  }
});
```

Create `frontend/src/types.ts`:

```ts
export type ReportSummary = {
  exists: boolean;
  missing_files: string[];
  data_quality: { ok: boolean; errors?: string[]; warnings?: string[] };
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
  rows: Record<string, string | number | boolean | null>[];
  errors: string[];
};
```

Create `frontend/src/api.ts`:

```ts
import type { ReportRun, ReportSummary, ReportTable } from "./types";

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function fetchSummary(): Promise<ReportSummary> {
  return getJson<ReportSummary>("/api/report/summary");
}

export function fetchRuns(): Promise<{ runs: ReportRun[] }> {
  return getJson<{ runs: ReportRun[] }>("/api/report/runs");
}

export function fetchTable(name: string): Promise<ReportTable> {
  return getJson<ReportTable>(`/api/report/tables/${name}`);
}

export async function refreshReport(): Promise<{ status: string; summary: ReportSummary }> {
  const response = await fetch("/api/report/run", { method: "POST" });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<{ status: string; summary: ReportSummary }>;
}
```

Create `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

Modify `.gitignore`:

```gitignore
frontend/node_modules/
frontend/dist/
frontend/.vite/
```

- [ ] **Step 2: Install frontend dependencies**

Run: `cd a_share_watchlist_report/frontend && npm install`

Expected: `package-lock.json` is generated.

- [ ] **Step 3: Build scaffold**

Run: `cd a_share_watchlist_report/frontend && npm run build`

Expected: FAIL because `src/App.tsx` and `src/styles.css` are not created yet.

## Task 4: Workbench UI Components

**Files:**
- Create: `a_share_watchlist_report/frontend/src/components/StatusBadge.tsx`
- Create: `a_share_watchlist_report/frontend/src/components/DataTable.tsx`
- Create: `a_share_watchlist_report/frontend/src/components/MetricStrip.tsx`
- Create: `a_share_watchlist_report/frontend/src/components/RunToolbar.tsx`
- Create: `a_share_watchlist_report/frontend/src/styles.css`
- Create: `a_share_watchlist_report/frontend/src/App.tsx`
- Test: `a_share_watchlist_report/frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing frontend tests**

Create `frontend/src/App.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";
import { App } from "./App";

const summary = {
  exists: true,
  missing_files: [],
  data_quality: { ok: true, warnings: [] },
  row_counts: {
    watchlist: 1,
    excluded_stocks: 2,
    holding_risk: 0,
    market_regime: 1
  },
  artifacts: {}
};

const table = {
  name: "watchlist",
  exists: true,
  columns: ["symbol", "name", "reason"],
  row_count: 1,
  rows: [{ symbol: "600519", name: "贵州茅台", reason: "12M 动量 10%" }],
  errors: []
};

describe("App", () => {
  test("renders the workbench shell and watchlist data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/summary")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(summary) });
        }
        if (url.endsWith("/runs")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ runs: [] }) });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve(table) });
      })
    );

    render(<App />);

    expect(screen.getByText("A-share Workbench")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("600519")).toBeInTheDocument());
    expect(screen.getByText("Data quality")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd a_share_watchlist_report/frontend && npm run test`

Expected: FAIL because `App.tsx` does not exist.

- [ ] **Step 3: Implement components and app**

Create `StatusBadge.tsx`:

```tsx
type StatusBadgeProps = {
  label: string;
  tone?: "ok" | "warn" | "bad" | "neutral";
};

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{label}</span>;
}
```

Create `DataTable.tsx`:

```tsx
import type { ReportTable } from "../types";

type DataTableProps = {
  table: ReportTable;
};

export function DataTable({ table }: DataTableProps) {
  if (!table.exists) {
    return <div className="empty-state">{table.errors[0] ?? "No table data"}</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {table.columns.map((column) => (
              <th key={column}>{column}</th>
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
```

Create `MetricStrip.tsx`:

```tsx
import type { ReportSummary } from "../types";

type MetricStripProps = {
  summary: ReportSummary | null;
};

export function MetricStrip({ summary }: MetricStripProps) {
  const counts = summary?.row_counts ?? {};
  return (
    <section className="metric-strip" aria-label="Report metrics">
      <div><span>Watchlist</span><strong>{counts.watchlist ?? 0}</strong></div>
      <div><span>Excluded</span><strong>{counts.excluded_stocks ?? 0}</strong></div>
      <div><span>Holding risk</span><strong>{counts.holding_risk ?? 0}</strong></div>
      <div><span>Regime rows</span><strong>{counts.market_regime ?? 0}</strong></div>
    </section>
  );
}
```

Create `RunToolbar.tsx`:

```tsx
import { RefreshCw } from "lucide-react";

type RunToolbarProps = {
  busy: boolean;
  onRefresh: () => void;
};

export function RunToolbar({ busy, onRefresh }: RunToolbarProps) {
  return (
    <div className="run-toolbar">
      <button type="button" onClick={onRefresh} disabled={busy} title="Refresh local report">
        <RefreshCw size={16} />
        <span>{busy ? "Refreshing" : "Refresh report"}</span>
      </button>
    </div>
  );
}
```

Create `App.tsx` with the workbench shell, summary load, table load for `watchlist`, `excluded_stocks`, `holding_risk`, `market_regime`, `dragon_tiger`, and refresh action. Use labels exactly:
- `A-share Workbench`
- `Run context`
- `Data quality`
- `Market regime`
- `Watchlist`
- `Excluded Stocks`
- `Holding Risk`
- `Dragon Tiger`

Create `styles.css` using the design tokens above. Keep tables dense, sticky headers, 8px or less border radius, clear focus states, no gradient blobs.

- [ ] **Step 4: Run frontend tests**

Run: `cd a_share_watchlist_report/frontend && npm run test`

Expected: PASS.

- [ ] **Step 5: Build frontend**

Run: `cd a_share_watchlist_report/frontend && npm run build`

Expected: PASS and writes `frontend/dist/`.

## Task 5: Documentation and Smoke Check

**Files:**
- Modify: `a_share_watchlist_report/README.md`

- [ ] **Step 1: Update README**

Add:

```markdown
## Local Frontend Workbench

Start the backend:

```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The frontend reads the existing report outputs through the local backend. It does not generate trading orders, target prices, or automated actions.
```

- [ ] **Step 2: Run full backend verification**

Run:

```bash
cd a_share_watchlist_report
python -m compileall .
pytest -q
python run_report.py
```

Expected:
- `compileall` exits 0.
- `pytest` exits 0.
- `run_report.py` exits 0 and generates the six P0 outputs.

- [ ] **Step 3: Run frontend verification**

Run:

```bash
cd a_share_watchlist_report/frontend
npm run test
npm run build
```

Expected:
- Vitest passes.
- TypeScript and Vite build pass.

- [ ] **Step 4: Manual local preview**

Run backend:

```bash
cd a_share_watchlist_report
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Run frontend in another shell:

```bash
cd a_share_watchlist_report/frontend
npm run dev
```

Expected:
- `http://127.0.0.1:5173` opens the workbench.
- The page shows `A-share Workbench`, `Data quality`, `Watchlist`, `Excluded Stocks`, `Holding Risk`, `Dragon Tiger`.
- Clicking refresh calls the backend and does not create trading language or order output.

## Self-Review Checklist

- V3 remains an additive frontend and table API layer.
- P0 static report files are still generated.
- V2 backend summary/run/history endpoints still work.
- No broker/account/order/BUY/SELL/target-price/ML/AI/backtest feature is introduced.
- Frontend is a dense workbench, not a landing page.
- Generated frontend artifacts and node dependencies are ignored by git.
