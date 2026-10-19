
import type { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
}: MetricCardProps) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-100">
            {value}
          </p>
          {subtitle && (
            <p className="mt-2 text-xs text-slate-500">{subtitle}</p>
          )}
        </div>

        {icon && (
          <div className="rounded-lg border border-slate-700 bg-slate-800 p-2 text-cyan-400">
            {icon}
          </div>
        )}
      </div>
    </section>
  );
}
