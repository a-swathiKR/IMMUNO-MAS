
import { Activity, Fingerprint, Radar } from "lucide-react";

interface BehavioralMonitoringProps {
  logs?: unknown[];
  anomalies?: unknown[];
  fingerprints?: unknown[];
  loading?: boolean;
  error?: string | null;
}

export default function BehavioralMonitoring({
  logs = [],
  anomalies = [],
  fingerprints = [],
  loading = false,
  error = null,
}: BehavioralMonitoringProps) {
  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          Behavioral Monitoring
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Review behavioral logs, anomaly records, and fingerprint data.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Metric
          title="Behavior Logs"
          value={logs.length}
          icon={<Activity size={20} />}
        />
        <Metric
          title="Anomaly Records"
          value={anomalies.length}
          icon={<Radar size={20} />}
        />
        <Metric
          title="Fingerprint Records"
          value={fingerprints.length}
          icon={<Fingerprint size={20} />}
        />
      </div>

      {loading && (
        <p className="text-sm text-slate-400">Loading behavioral data…</p>
      )}

      {error && (
        <p className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </p>
      )}

      <DataSection title="Behavior Logs" records={logs} />
      <DataSection title="Detected Anomalies" records={anomalies} />
      <DataSection title="Behavioral Fingerprints" records={fingerprints} />
    </div>
  );
}

function Metric({
  title,
  value,
  icon,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <span className="text-cyan-400">{icon}</span>
      </div>
      <p className="mt-3 text-2xl font-semibold text-slate-100">{value}</p>
    </section>
  );
}

function DataSection({
  title,
  records,
}: {
  title: string;
  records: unknown[];
}) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/60">
      <div className="border-b border-slate-800 px-5 py-4">
        <h3 className="font-semibold text-slate-100">{title}</h3>
      </div>

      {records.length === 0 ? (
        <p className="p-5 text-sm text-slate-500">
          No records supplied to this page.
        </p>
      ) : (
        <div className="max-h-80 overflow-auto p-5">
          <pre className="whitespace-pre-wrap break-words text-xs leading-6 text-slate-300">
            {JSON.stringify(records, null, 2)}
          </pre>
        </div>
      )}
    </section>
  );
}
