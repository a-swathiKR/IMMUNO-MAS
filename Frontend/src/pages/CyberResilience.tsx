
import { Activity, ShieldCheck, ShieldAlert } from "lucide-react";

interface CyberResilienceProps {
  resilienceStatus?: unknown;
  backendOnline: boolean;
  loading?: boolean;
  error?: string | null;
}

export default function CyberResilience({
  resilienceStatus,
  backendOnline,
  loading = false,
  error = null,
}: CyberResilienceProps) {
  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          Cyber Resilience
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Inspect backend availability and reported resilience information.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3">
            <ShieldCheck size={21} className="text-cyan-400" />
            <p className="text-sm text-slate-400">Backend Connectivity</p>
          </div>
          <p
            className={`mt-3 text-xl font-semibold ${
              backendOnline ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {backendOnline ? "Online" : "Offline"}
          </p>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3">
            <Activity size={21} className="text-cyan-400" />
            <p className="text-sm text-slate-400">Resilience Status</p>
          </div>
          <p className="mt-3 text-xl font-semibold text-slate-100">
            {resilienceStatus == null ? "Not loaded" : "Data available"}
          </p>
        </section>
      </div>

      {loading && (
        <p className="text-sm text-slate-400">
          Loading resilience information…
        </p>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          <ShieldAlert size={18} className="mt-0.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <section className="rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="border-b border-slate-800 px-5 py-4">
          <h3 className="font-semibold text-slate-100">
            Backend Resilience Data
          </h3>
        </div>

        {resilienceStatus == null ? (
          <p className="p-5 text-sm text-slate-400">
            No resilience data has been supplied to this page.
          </p>
        ) : (
          <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap break-words p-5 text-xs leading-6 text-slate-300">
            {JSON.stringify(resilienceStatus, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}
