import StatusBadge from "../components/StatusBadge";
import type { Agent } from "../types";

interface AgentManagementProps {
  agents: Agent[];
  loading?: boolean;
  error?: string | null;
}

export default function AgentManagement({
  agents,
  loading = false,
  error = null,
}: AgentManagementProps) {
  const healthyCount = agents.filter((agent) =>
    ["HEALTHY", "ACTIVE", "ONLINE", "OPERATIONAL"].includes(
      agent.status.toUpperCase(),
    ),
  ).length;

  const standbyCount = agents.filter(
    (agent) => agent.status.toUpperCase() === "STANDBY",
  ).length;

  const backupCount = agents.filter(
    (agent) =>
      agent.designation.toUpperCase().includes("BACKUP") ||
      agent.agent_id.toUpperCase().endsWith("-02"),
  ).length;

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          Agent Management
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Inspect agent identities, roles, availability, and status reported by
          the IMMUNO-MAS backend.
        </p>
      </section>

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-sm text-slate-400">Total Agents</p>
          <p className="mt-2 text-2xl font-semibold text-slate-100">
            {loading && agents.length === 0 ? "—" : agents.length}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Records returned by the backend
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-sm text-slate-400">Healthy Agents</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-400">
            {healthyCount}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Reporting a healthy or active status
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-sm text-slate-400">Standby Agents</p>
          <p className="mt-2 text-2xl font-semibold text-sky-400">
            {standbyCount}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Reporting standby status
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <p className="text-sm text-slate-400">Backup Agents</p>
          <p className="mt-2 text-2xl font-semibold text-cyan-400">
            {backupCount}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Identified from designation or agent ID
          </p>
        </div>
      </div>

      {/* Agent records */}
      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex flex-col gap-2 border-b border-slate-800 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="font-semibold text-slate-100">Registered Agents</h3>
            <p className="mt-1 text-xs text-slate-400">
              Live records from GET /agents
            </p>
          </div>

          <span className="w-fit rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
            {agents.length} records
          </span>
        </div>

        {loading && agents.length === 0 ? (
          <p className="p-5 text-sm text-slate-400">
            Loading agents from the backend…
          </p>
        ) : error ? (
          <div className="p-5">
            <p className="text-sm font-medium text-red-400">
              Unable to load agent data
            </p>
            <p className="mt-1 break-words text-xs text-slate-400">{error}</p>
          </div>
        ) : agents.length === 0 ? (
          <p className="p-5 text-sm text-slate-400">
            No agent records were returned by the backend.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-left text-sm">
              <thead className="bg-slate-950/50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-5 py-3">Agent ID</th>
                  <th className="px-5 py-3">Agent Name</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Designation</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Warnings</th>
                  <th className="px-5 py-3 text-right">Quarantines</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800">
                {agents.map((agent) => (
                  <tr
                    key={agent.agent_id}
                    className="transition-colors hover:bg-white/[0.02]"
                  >
                    <td className="px-5 py-4 font-mono text-cyan-300">
                      {agent.agent_id}
                    </td>

                    <td className="px-5 py-4 font-medium text-slate-200">
                      {agent.name}
                    </td>

                    <td className="px-5 py-4 text-slate-400">
                      {agent.role || "—"}
                    </td>

                    <td className="px-5 py-4">
                      <span className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-400">
                        {agent.designation || "—"}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <StatusBadge status={agent.status} />
                    </td>

                    <td className="px-5 py-4 text-right tabular-nums text-slate-300">
                      {agent.total_warnings}
                    </td>

                    <td className="px-5 py-4 text-right tabular-nums text-slate-300">
                      {agent.total_quarantines}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="border-t border-slate-800 px-5 py-3">
          <p className="text-xs leading-5 text-slate-500">
            Status and counters reflect the values available in the backend
            response. This page does not trigger recovery, quarantine, or
            failover operations.
          </p>
        </div>
      </section>
    </div>
  );
}
