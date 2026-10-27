import MetricCard from "../components/MetricCard";
import { Activity, Network, ShieldAlert, ShieldCheck } from "lucide-react";
import type { Agent } from "../types";

interface OverviewProps {
  agents: Agent[];
  backendOnline: boolean;
  activeBackups: Record<string, string>;
}

export default function Overview({
  agents,
  backendOnline,
  activeBackups,
}: OverviewProps) {
  const healthyAgents = agents.filter(
    (agent) => agent.status.toUpperCase() === "HEALTHY",
  ).length;

  const standbyAgents = agents.filter(
    (agent) => agent.status.toUpperCase() === "STANDBY",
  ).length;

  const activeBackupIds = new Set(Object.values(activeBackups));

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-100">
          System Overview
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Live summary of the IMMUNO-MAS multi-agent system.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Registered Agents"
          value={agents.length}
          subtitle="Records returned by the backend"
          icon={<Network size={20} />}
        />

        <MetricCard
          title="Healthy Agents"
          value={healthyAgents}
          subtitle="Currently reporting HEALTHY"
          icon={<ShieldCheck size={20} />}
        />

        <MetricCard
          title="Standby Agents"
          value={standbyAgents}
          subtitle="Available as configured backups"
          icon={<Activity size={20} />}
        />

        <MetricCard
          title="Backend Status"
          value={backendOnline ? "Online" : "Offline"}
          subtitle="Based on the latest health check"
          icon={<ShieldAlert size={20} />}
        />
      </div>

      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="border-b border-slate-800 px-5 py-4">
          <h3 className="font-semibold text-slate-100">Agent Status</h3>
          <p className="mt-1 text-xs text-slate-400">
            Live agent health and operational backup status.
          </p>
        </div>

        {agents.length === 0 ? (
          <p className="p-5 text-sm text-slate-400">
            No agent records are available.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-5 py-3">Agent ID</th>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800">
                {agents.map((agent) => {
                  const agentId = agent.id;
                  const isActiveBackup = activeBackupIds.has(agentId);
                  const displayedStatus = isActiveBackup
                    ? "ACTIVE BACKUP"
                    : agent.status;

                  return (
                    <tr key={agent.id}>
                      <td className="px-5 py-4 font-mono text-cyan-300">
                        {agent.id}
                      </td>
                      <td className="px-5 py-4 text-slate-200">{agent.name}</td>
                      <td className="px-5 py-4 text-slate-400">
                        {agent.role || "—"}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`rounded-full border px-2.5 py-1 text-xs ${
                            isActiveBackup
                              ? "border-cyan-700 bg-cyan-950/40 text-cyan-300"
                              : "border-slate-700 text-slate-300"
                          }`}
                        >
                          {displayedStatus}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
