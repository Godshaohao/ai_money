import { RefreshCw } from "lucide-react";

type RunToolbarProps = {
  busy: boolean;
  onRefresh: () => void;
};

export function RunToolbar({ busy, onRefresh }: RunToolbarProps) {
  return (
    <div className="run-toolbar">
      <button type="button" onClick={onRefresh} disabled={busy} title="刷新本地报告">
        <RefreshCw size={16} />
        <span>{busy ? "刷新中" : "刷新报告"}</span>
      </button>
    </div>
  );
}
