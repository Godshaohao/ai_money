import type { ReportTable } from "../types";

type DataTableProps = {
  table: ReportTable | null;
};

export function DataTable({ table }: DataTableProps) {
  if (table === null) {
    return <div className="empty-state">Loading table</div>;
  }

  if (!table.exists) {
    return <div className="empty-state">{table.errors[0] ?? "No table data"}</div>;
  }

  if (table.columns.length === 0) {
    return <div className="empty-state">No rows</div>;
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
