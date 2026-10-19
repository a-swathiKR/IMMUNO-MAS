
import { Settings as SettingsIcon, Server, ShieldCheck } from "lucide-react";

interface SettingsProps {
  settings?: unknown;
  loading?: boolean;
  error?: string | null;
}

export default function Settings({
  settings,
  loading = false,
  error = null,
}: SettingsProps) {
  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          Settings
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          View the configuration information exposed by the backend.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3">
            <Server size={20} className="text-cyan-400" />
            <p className="text-sm text-slate-400">Configuration Source</p>
          </div>
          <p className="mt-3 font-semibold text-slate-100">
            Backend API
          </p>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-3">
            <ShieldCheck size={20} className="text-cyan-400" />
            <p className="text-sm text-slate-400">Settings Data</p>
          </div>
          <p className="mt-3 font-semibold text-slate-100">
            {settings == null ? "Not loaded" : "Available"}
          </p>
        </section>
      </div>

      {loading && (
        <p className="text-sm text-slate-400">Loading settings…</p>
      )}

      {error && (
        <p className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </p>
      )}

      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2 border-b border-slate-800 px-5 py-4">
          <SettingsIcon size={18} className="text-cyan-400" />
          <h3 className="font-semibold text-slate-100">
            Backend Configuration
          </h3>
        </div>

        {settings == null ? (
          <p className="p-5 text-sm text-slate-400">
            No settings data has been supplied to this page.
          </p>
        ) : (
          <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap break-words p-5 text-xs leading-6 text-slate-300">
            {JSON.stringify(settings, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}
