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
