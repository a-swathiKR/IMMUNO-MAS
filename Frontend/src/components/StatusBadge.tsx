
interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normalizedStatus = status.toUpperCase();

  const colorClass =
    normalizedStatus === "HEALTHY" ||
    normalizedStatus === "ACTIVE" ||
    normalizedStatus === "ONLINE" ||
    normalizedStatus === "PRIMARY"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
      : normalizedStatus === "STANDBY"
        ? "border-sky-500/30 bg-sky-500/10 text-sky-400"
        : normalizedStatus === "WARNING"
          ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
          : normalizedStatus === "QUARANTINED" ||
              normalizedStatus === "FAILED" ||
              normalizedStatus === "OFFLINE"
            ? "border-red-500/30 bg-red-500/10 text-red-400"
            : "border-slate-500/30 bg-slate-500/10 text-slate-400";

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${colorClass}`}
    >
      <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}
