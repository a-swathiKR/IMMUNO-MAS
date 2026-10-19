
import { ShieldAlert, AlertTriangle } from "lucide-react";

interface ThreatDetectionProps {
  anomalies?: unknown[];
  loading?: boolean;
  error?: string | null;
}

export default function ThreatDetection({
  anomalies = [],
  loading = false,
  error = null,
}: ThreatDetectionProps) {
  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          Threat Detection
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Review anomaly records reported by the behavioral monitoring system.
        </p>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-amber-500/10 p-3 text-amber-400">
            <ShieldAlert size={22} />
          </div>
          <div>
            <p className="text-sm text-slate-400">Anomaly records received</p>
            <p className="mt-1 text-2xl font-semibold text-slate-100">
              {anomalies.length}
            </p>
          </div>
        </div>
      </section>

      {loading && (
        <p className="text-sm text-slate-400">Loading threat data…</p>
      )}

      {error && (
        <p className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </p>
      )}

      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2 border-b border-slate-800 px-5 py-4">
          <AlertTriangle size={17} className="text-amber-400" />
          <h3 className="font-semibold text-slate-100">Anomaly Records</h3>
        </div>

        {anomalies.length === 0 ? (
          <p className="p-5 text-sm text-slate-400">
            No anomaly records have been supplied to this page. This does not
            necessarily mean that the system has no threats.
          </p>
        ) : (
          <div className="max-h-[520px] overflow-auto p-5">
            <pre className="whitespace-pre-wrap break-words text-xs leading-6 text-slate-300">
              {JSON.stringify(anomalies, null, 2)}
            </pre>
          </div>
        )}
      </section>
    </div>
  );
}
