
import { RefreshCw, ShieldCheck, Server } from "lucide-react";

interface FailoverRecoveryProps {
  resilienceStatus?: unknown;
  events?: unknown[];
  loading?: boolean;
  error?: string | null;
}

export default function FailoverRecovery({
  resilienceStatus,
  events = [],
  loading = false,
  error = null,
}: FailoverRecoveryProps) {
  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          Failover & Recovery
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Inspect reported recovery status and resilience events.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3">
            <Server size={20} className="text-cyan-400" />
            <p className="text-sm text-slate-400">Resilience Status</p>
          </div>
          <p className="mt-3 text-lg font-semibold text-slate-100">
            {resilienceStatus == null ? "Not loaded" : "Data available"}
          </p>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3">
            <ShieldCheck size={20} className="text-cyan-400" />
            <p className="text-sm text-slate-400">Reported Events</p>
          </div>
          <p className="mt-3 text-2xl font-semibold text-slate-100">
            {events.length}
          </p>
        </section>
      </div>

      {loading && (
        <p className="text-sm text-slate-400">
          Loading recovery information…
        </p>
      )}

      {error && (
        <p className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </p>
      )}

      <section className="rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2 border-b border-slate-800 px-5 py-4">
          <RefreshCw size={17} className="text-cyan-400" />
          <h3 className="font-semibold text-slate-100">Recovery Events</h3>
        </div>

        {events.length === 0 ? (
          <p className="p-5 text-sm text-slate-400">
            No recovery events have been supplied to this page. This does not
            establish that a recovery operation has or has not occurred.
          </p>
        ) : (
          <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-words p-5 text-xs leading-6 text-slate-300">
            {JSON.stringify(events, null, 2)}
          </pre>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="border-b border-slate-800 px-5 py-4">
          <h3 className="font-semibold text-slate-100">
            Resilience Details
          </h3>
        </div>

        {resilienceStatus == null ? (
          <p className="p-5 text-sm text-slate-400">
            No resilience status has been supplied.
          </p>
        ) : (
          <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-words p-5 text-xs leading-6 text-slate-300">
            {JSON.stringify(resilienceStatus, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}
