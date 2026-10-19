
import { ClipboardList, FileText } from "lucide-react";

interface AuditLogsProps {
  logs?: unknown[];
  loading?: boolean;
  error?: string | null;
}

export default function AuditLogs({
  logs = [],
  loading = false,
  error = null,
}: AuditLogsProps) {
  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          Audit Logs
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Review log records supplied by the backend for project auditing.
        </p>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex items-center gap-3">
          <ClipboardList size={22} className="text-cyan-400" />
          <div>
            <p className="text-sm text-slate-400">Records received</p>
            <p className="mt-1 text-2xl font-semibold text-slate-100">
              {logs.length}
            </p>
          </div>
        </div>
      </section>

      {loading && (
        <p className="text-sm text-slate-400">Loading audit records…</p>
      )}

      {error && (
        <p className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </p>
      )}

      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2 border-b border-slate-800 px-5 py-4">
          <FileText size={17} className="text-cyan-400" />
          <h3 className="font-semibold text-slate-100">Log Records</h3>
        </div>

        {logs.length === 0 ? (
          <p className="p-5 text-sm text-slate-400">
            No log records have been supplied to this page.
          </p>
        ) : (
          <div className="max-h-[560px] overflow-auto p-5">
            <pre className="whitespace-pre-wrap break-words text-xs leading-6 text-slate-300">
              {JSON.stringify(logs, null, 2)}
            </pre>
          </div>
        )}
      </section>
    </div>
  );
}
