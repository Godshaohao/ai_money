type StatusBadgeProps = {
  label: string;
  tone?: "ok" | "warn" | "bad" | "neutral";
};

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{label}</span>;
}
