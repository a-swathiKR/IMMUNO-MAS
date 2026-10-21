import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  Shield,
  LayoutDashboard,
  Bot,
  Fingerprint,
  AlertTriangle,
  RefreshCw,
  ScrollText,
  Settings,
  Bell,
  Search,
  Menu,
  ShieldCheck,
  Zap,
  Network,
  Clock3,
  CircleCheck,
  CircleAlert,
  ArrowUpRight,
  Server,
  Wifi,
  WifiOff,
  ChevronRight,
  LockKeyhole,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

type Agent = {
  agent_id: string;
  name: string;
  role: string;
  status: string;
  raw_status: string;
  designation: string;
  warn_count: number;
  total_warnings: number;
  total_quarantines: number;
  is_active_backup: boolean;
  available: boolean;
};

type HealthResponse = {
  status: string;
  timestamp?: string;
  version?: string;
  system?: string;
};

type NavigationItem = {
  label: string;
  icon: typeof LayoutDashboard;
};

const navigation: NavigationItem[] = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Agent Management", icon: Bot },
  { label: "Behavioral Monitoring", icon: Fingerprint },
  { label: "Threat Detection", icon: AlertTriangle },
  { label: "Cyber Resilience", icon: ShieldCheck },
  { label: "Failover & Recovery", icon: RefreshCw },
  { label: "Audit Logs", icon: ScrollText },
  { label: "Settings", icon: Settings },
];

function readString(
  item: Record<string, unknown>,
  keys: string[],
  fallback: string,
): string {
  for (const key of keys) {
    const value = item[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return fallback;
}

function readNumber(item: Record<string, unknown>, keys: string[]): number {
  for (const key of keys) {
    const value = item[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
  }
  return 0;
}

function readBoolean(item: Record<string, unknown>, keys: string[]): boolean {
  for (const key of keys) {
    const value = item[key];
    if (typeof value === "boolean") return value;
  }
  return false;
}

function normalizeAgent(value: unknown, index: number): Agent {
  const item =
    value && typeof value === "object"
      ? (value as Record<string, unknown>)
      : {};

  const agentId = readString(
    item,
    ["agent_id", "id", "agentId", "name"],
    `Agent ${index + 1}`,
  );

  const rawStatus = readString(
    item,
    ["raw_status", "status", "state"],
    "UNKNOWN",
  );

  const status = rawStatus.toUpperCase();

  return {
    agent_id: agentId,
    name: readString(item, ["name", "agent_name", "display_name"], agentId),
    role: readString(
      item,
      ["role", "description", "agent_type", "type"],
      "Autonomous agent",
    ),
    status: rawStatus,
    raw_status: rawStatus,
    designation: readString(
      item,
      ["designation", "agent_designation", "category"],
      agentId.toUpperCase().includes("BACKUP") ||
        agentId.toUpperCase().endsWith("-02")
        ? "BACKUP"
        : "PRIMARY",
    ),
    warn_count: readNumber(item, ["warn_count", "warning_count"]),
    total_warnings: readNumber(item, [
      "total_warnings",
      "warning_count",
      "warn_count",
    ]),
    total_quarantines: readNumber(item, [
      "total_quarantines",
      "quarantine_count",
    ]),
    is_active_backup: readBoolean(item, ["is_active_backup"]),
    available:
      typeof item.available === "boolean"
        ? item.available
        : ["HEALTHY", "ACTIVE", "ONLINE", "STANDBY"].includes(status),
  };
}

function getStatusStyle(status: string) {
  const normalized = status.toUpperCase();

  if (
    ["HEALTHY", "ACTIVE", "ONLINE", "CONNECTED", "OPERATIONAL"].includes(
      normalized,
    )
  ) {
    return {
      color: "text-emerald-300",
      background: "bg-emerald-400/10",
      dot: "bg-emerald-400",
    };
  }

  if (["STANDBY", "IDLE", "READY"].includes(normalized)) {
    return {
      color: "text-sky-300",
      background: "bg-sky-400/10",
      dot: "bg-sky-400",
    };
  }

  if (["WARNING", "DEGRADED", "SUSPECT", "RECOVERING"].includes(normalized)) {
    return {
      color: "text-amber-300",
      background: "bg-amber-400/10",
      dot: "bg-amber-400",
    };
  }

  if (["QUARANTINED", "FAILED", "OFFLINE", "ERROR"].includes(normalized)) {
    return {
      color: "text-rose-300",
      background: "bg-rose-400/10",
      dot: "bg-rose-400",
    };
  }

  return {
    color: "text-slate-300",
    background: "bg-slate-400/10",
    dot: "bg-slate-400",
  };
}

function StatusBadge({ status }: { status: string }) {
  const style = getStatusStyle(status);

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-medium ${style.color} ${style.background}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {status.replaceAll("_", " ")}
    </span>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: typeof Activity;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-[#101621] p-5 transition-colors hover:border-white/[0.13]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-100">
            {value}
          </p>
        </div>
        <div className={`rounded-xl p-3 ${accent}`}>
          <Icon size={20} />
        </div>
      </div>
      <p className="mt-4 text-xs text-slate-500">{subtitle}</p>
    </div>
  );
}

function App() {
  const [activePage, setActivePage] = useState("Overview");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const loadBackendData = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setApiError("");

    try {
      const [agentsResponse, healthResponse] = await Promise.all([
        fetch(`${API_BASE}/agents`, { signal }),
        fetch(`${API_BASE}/health`, { signal }),
      ]);

      if (!agentsResponse.ok) {
        throw new Error(`/agents returned HTTP ${agentsResponse.status}`);
      }

      if (!healthResponse.ok) {
        throw new Error(`/health returned HTTP ${healthResponse.status}`);
      }

      const agentData: unknown = await agentsResponse.json();
      const healthData: HealthResponse = await healthResponse.json();

      let agentList: unknown[] = [];

      if (Array.isArray(agentData)) {
        agentList = agentData;
      } else if (
        agentData &&
        typeof agentData === "object" &&
        "agents" in agentData &&
        Array.isArray((agentData as { agents: unknown[] }).agents)
      ) {
        agentList = (agentData as { agents: unknown[] }).agents;
      }

      setAgents(agentList.map(normalizeAgent));
      setHealth(healthData);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      if (error instanceof Error && error.name !== "AbortError") {
        setApiError(
          `${error.message}. Check that the FastAPI backend is running at ${API_BASE}.`,
        );
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadBackendData(controller.signal);

    return () => controller.abort();
  }, [loadBackendData]);

  const healthyCount = agents.filter((agent) =>
    ["HEALTHY", "ACTIVE", "ONLINE", "OPERATIONAL"].includes(
      agent.status.toUpperCase(),
    ),
  ).length;

  const backupCount = agents.filter(
    (agent) =>
      agent.designation.toUpperCase().includes("BACKUP") ||
      agent.agent_id.toUpperCase().endsWith("-02"),
  ).length;

  const warningCount = agents.reduce(
    (total, agent) => total + agent.total_warnings,
    0,
  );

  const quarantineCount = agents.reduce(
    (total, agent) => total + agent.total_quarantines,
    0,
  );

  const backendOnline =
    health?.status?.toUpperCase() === "ONLINE" ||
    health?.status?.toUpperCase() === "HEALTHY";

  const showOverview = activePage === "Overview";

  return (
    <div className="flex min-h-screen bg-[#080b12] text-slate-100">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-[76px]"
        } fixed inset-y-0 left-0 z-30 flex flex-col border-r border-white/[0.07] bg-[#0b1019] transition-all duration-200 lg:sticky lg:top-0 lg:h-screen`}
      >
        <div className="flex h-[76px] items-center gap-3 border-b border-white/[0.07] px-5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300 ring-1 ring-cyan-300/20">
            <Shield size={23} />
          </div>
          {sidebarOpen && (
            <div className="min-w-0">
              <p className="text-sm font-bold tracking-wide text-white">
                AI-DNA SHIELD
              </p>
              <p className="mt-0.5 text-[10px] uppercase tracking-[0.18em] text-slate-500">
                IMMUNO-MAS
              </p>
            </div>
          )}
        </div>

        <div className="px-3 pt-6">
          {sidebarOpen && (
            <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">
              Security Console
            </p>
          )}

          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = activePage === item.label;

              return (
                <button
                  key={item.label}
                  onClick={() => setActivePage(item.label)}
                  title={!sidebarOpen ? item.label : undefined}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition-colors ${
                    active
                      ? "border border-cyan-300/15 bg-cyan-300/10 text-cyan-200"
                      : "border border-transparent text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                  }`}
                >
                  <Icon size={18} className="shrink-0" />
                  {sidebarOpen && (
                    <>
                      <span className="flex-1">{item.label}</span>
                      {active && <ChevronRight size={14} />}
                    </>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto p-4">
          {sidebarOpen && (
            <div className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <LockKeyhole size={14} className="text-cyan-300" />
                Resilience Framework
              </div>
              <p className="mt-2 text-[11px] leading-5 text-slate-500">
                Behavioral identity and autonomous recovery monitoring.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    backendOnline ? "bg-emerald-400" : "bg-slate-500"
                  }`}
                />
                <span className="text-[10px] text-slate-500">
                  {backendOnline
                    ? "Backend connected"
                    : "Connection unverified"}
                </span>
              </div>
            </div>
          )}
          {sidebarOpen && (
            <p className="mt-4 text-center text-[10px] text-slate-600">
              AI-DNA SHIELD · v2.0.0
            </p>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="min-w-0 flex-1">
        {/* Header */}
        <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between gap-4 border-b border-white/[0.07] bg-[#080b12]/90 px-5 backdrop-blur-xl sm:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <button
              onClick={() => setSidebarOpen((open) => !open)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-white/[0.06] hover:text-white"
              aria-label="Toggle sidebar"
            >
              <Menu size={20} />
            </button>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-semibold text-white">
                  {activePage}
                </span>
                <span className="hidden rounded-md border border-white/[0.08] px-2 py-0.5 text-[10px] text-slate-500 sm:inline-flex">
                  IMMUNO-MAS
                </span>
              </div>
              <p className="mt-1 hidden text-xs text-slate-500 sm:block">
                Autonomous multi-agent security and resilience
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-white/[0.07] bg-white/[0.025] px-3 py-2 sm:flex">
              {backendOnline ? (
                <Wifi size={14} className="text-emerald-400" />
              ) : (
                <WifiOff size={14} className="text-slate-500" />
              )}
              <span className="text-xs text-slate-400">
                {backendOnline ? "API Online" : "API Unverified"}
              </span>
            </div>
            <button
              onClick={() => void loadBackendData()}
              disabled={loading}
              title="Refresh backend data"
              className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2.5 text-xs text-slate-300 transition-colors hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
            <button
              title="Notifications"
              className="relative rounded-xl border border-white/[0.08] bg-white/[0.03] p-2.5 text-slate-400 hover:text-white"
            >
              <Bell size={17} />
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1600px] p-5 sm:p-8">
          {/* Page introduction */}
          <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <div className="mb-2 flex items-center gap-2 text-xs text-slate-500">
                <span>Security Console</span>
                <ChevronRight size={12} />
                <span className="text-cyan-300">{activePage}</span>
              </div>
              <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                {showOverview ? "System Overview" : activePage}
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                {showOverview
                  ? "Monitor agent availability and inspect the current status reported by your resilience backend."
                  : `Explore the ${activePage.toLowerCase()} area of the AI-DNA SHIELD console.`}
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Clock3 size={14} />
              {lastUpdated
                ? `Last updated ${lastUpdated}`
                : "Waiting for backend data"}
            </div>
          </div>

          {/* Backend error */}
          {apiError && (
            <div className="mb-6 flex flex-col gap-3 rounded-xl border border-rose-400/20 bg-rose-400/[0.06] p-4 sm:flex-row sm:items-start">
              <CircleAlert size={19} className="shrink-0 text-rose-300" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-rose-200">
                  Unable to load backend data
                </p>
                <p className="mt-1 break-words text-xs leading-5 text-rose-200/70">
                  {apiError}
                </p>
              </div>
              <button
                onClick={() => void loadBackendData()}
                className="self-start rounded-lg border border-rose-300/20 px-3 py-2 text-xs text-rose-200 hover:bg-rose-300/10"
              >
                Try again
              </button>
            </div>
          )}

          {showOverview ? (
            <>
              {/* Metric cards */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  title="Configured Agents"
                  value={
                    loading && agents.length === 0
                      ? "—"
                      : String(agents.length).padStart(2, "0")
                  }
                  subtitle="Reported by the backend /agents endpoint"
                  icon={Bot}
                  accent="bg-cyan-400/10 text-cyan-300"
                />
                <MetricCard
                  title="Healthy Agents"
                  value={
                    loading && agents.length === 0
                      ? "—"
                      : `${healthyCount}`.padStart(2, "0")
                  }
                  subtitle="Currently reporting a healthy or active state"
                  icon={Activity}
                  accent="bg-emerald-400/10 text-emerald-300"
                />
                <MetricCard
                  title="Warnings"
                  value={
                    loading && agents.length === 0 ? "—" : String(warningCount)
                  }
                  subtitle="Sum of warning counters exposed by agents"
                  icon={AlertTriangle}
                  accent="bg-amber-400/10 text-amber-300"
                />
                <MetricCard
                  title="Quarantines"
                  value={
                    loading && agents.length === 0
                      ? "—"
                      : String(quarantineCount)
                  }
                  subtitle="Sum of quarantine counters exposed by agents"
                  icon={ShieldCheck}
                  accent="bg-violet-400/10 text-violet-300"
                />
              </div>

              {/* System health and topology */}
              <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
                <section className="rounded-2xl border border-white/[0.07] bg-[#101621] p-5 xl:col-span-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="font-semibold text-white">
                        Agent Network
                      </h2>
                      <p className="mt-1 text-xs text-slate-500">
                        Agents discovered from the live backend response
                      </p>
                    </div>
                    <div className="flex items-center gap-2 rounded-lg border border-white/[0.07] px-3 py-2 text-xs text-slate-400">
                      <Network size={14} className="text-cyan-300" />
                      {agents.length} agents
                    </div>
                  </div>

                  <div className="my-5 flex flex-col items-center">
                    <div className="flex w-full max-w-xs items-center gap-3 rounded-xl border border-cyan-300/20 bg-cyan-300/[0.06] p-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-300/10 text-cyan-200">
                        <Shield size={21} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-slate-100">
                          AI-DNA SHIELD
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          {health?.system || "Resilience backend"}
                        </p>
                      </div>
                      <span
                        className={`h-2 w-2 rounded-full ${
                          backendOnline ? "bg-emerald-400" : "bg-slate-500"
                        }`}
                      />
                    </div>

                    <div className="h-7 w-px bg-slate-700" />
                    <div className="h-px w-full max-w-md bg-slate-700" />
                    <div className="grid w-full grid-cols-1 gap-3 pt-4 sm:grid-cols-2">
                      {loading && agents.length === 0 ? (
                        <div className="col-span-full py-8 text-center text-sm text-slate-500">
                          Loading agents from backend…
                        </div>
                      ) : agents.length === 0 ? (
                        <div className="col-span-full rounded-xl border border-dashed border-white/10 p-6 text-center">
                          <Server
                            size={22}
                            className="mx-auto text-slate-500"
                          />
                          <p className="mt-3 text-sm text-slate-400">
                            No agents returned
                          </p>
                          <p className="mt-1 text-xs text-slate-600">
                            Check the response from the /agents endpoint.
                          </p>
                        </div>
                      ) : (
                        agents.map((agent) => (
                          <div
                            key={agent.agent_id}
                            className="flex min-w-0 items-center gap-3 rounded-xl border border-white/[0.07] bg-[#0b1019] p-3"
                          >
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-slate-300">
                              <Bot size={18} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="truncate text-xs font-medium text-slate-200">
                                {agent.name}
                              </p>
                              <p className="mt-1 truncate text-[10px] text-slate-500">
                                {agent.agent_id} · {agent.role}
                              </p>
                            </div>
                            <span
                              className={`h-2 w-2 shrink-0 rounded-full ${
                                getStatusStyle(agent.status).dot
                              }`}
                              title={agent.status}
                            />
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </section>

                {/* Backend health */}
                <section className="rounded-2xl border border-white/[0.07] bg-[#101621] p-5">
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-emerald-400/10 p-3 text-emerald-300">
                      <Server size={20} />
                    </div>
                    <div>
                      <h2 className="font-semibold text-white">
                        Backend Health
                      </h2>
                      <p className="mt-1 text-xs text-slate-500">
                        FastAPI service
                      </p>
                    </div>
                  </div>

                  <div className="mt-6 rounded-xl border border-white/[0.06] bg-[#0b1019] p-4">
                    <p className="text-xs text-slate-500">Reported status</p>
                    <div className="mt-2">
                      {health ? (
                        <StatusBadge status={health.status} />
                      ) : (
                        <StatusBadge
                          status={loading ? "CHECKING" : "UNKNOWN"}
                        />
                      )}
                    </div>
                    <p className="mt-3 break-all text-xs leading-5 text-slate-500">
                      {API_BASE}
                    </p>
                  </div>

                  <div className="mt-4 space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs text-slate-400">
                        API response
                      </span>
                      <span className="text-xs text-slate-300">
                        {health
                          ? "Received"
                          : loading
                            ? "Checking…"
                            : "Unavailable"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs text-slate-400">Version</span>
                      <span className="text-xs text-slate-300">
                        {health?.version || "Not reported"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs text-slate-400">
                        Backup agents
                      </span>
                      <span className="text-xs text-slate-300">
                        {agents.length ? backupCount : "—"}
                      </span>
                    </div>
                  </div>

                  <div className="mt-6 border-t border-white/[0.07] pt-4">
                    <div className="flex items-start gap-2">
                      {health ? (
                        <CircleCheck
                          size={16}
                          className="mt-0.5 shrink-0 text-emerald-300"
                        />
                      ) : (
                        <CircleAlert
                          size={16}
                          className="mt-0.5 shrink-0 text-amber-300"
                        />
                      )}
                      <p className="text-xs leading-5 text-slate-400">
                        {health
                          ? "Health data was received from the backend. This does not by itself verify every resilience feature."
                          : "The dashboard is waiting for a successful health response."}
                      </p>
                    </div>
                  </div>
                </section>
              </div>

              {/* Agent table */}
              <section className="mt-6 overflow-hidden rounded-2xl border border-white/[0.07] bg-[#101621]">
                <div className="flex flex-col gap-3 border-b border-white/[0.07] p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="font-semibold text-white">
                      Configured Agents
                    </h2>
                    <p className="mt-1 text-xs text-slate-500">
                      Live data from GET /agents
                    </p>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg border border-white/[0.07] bg-[#0b1019] px-3 py-2">
                    <Search size={14} className="text-slate-500" />
                    <span className="text-xs text-slate-500">
                      {agents.length} records
                    </span>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full min-w-[700px] text-left">
                    <thead>
                      <tr className="border-b border-white/[0.06] bg-white/[0.015]">
                        <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                          Agent
                        </th>
                        <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                          Role
                        </th>
                        <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                          Designation
                        </th>
                        <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                          Status
                        </th>
                        <th className="px-5 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                          Warnings
                        </th>
                        <th className="px-5 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                          Quarantines
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.05]">
                      {loading && agents.length === 0 ? (
                        <tr>
                          <td
                            colSpan={6}
                            className="px-5 py-12 text-center text-sm text-slate-500"
                          >
                            Loading agent data…
                          </td>
                        </tr>
                      ) : agents.length === 0 ? (
                        <tr>
                          <td
                            colSpan={6}
                            className="px-5 py-12 text-center text-sm text-slate-500"
                          >
                            No agent data is currently available.
                          </td>
                        </tr>
                      ) : (
                        agents.map((agent) => (
                          <tr
                            key={agent.agent_id}
                            className="transition-colors hover:bg-white/[0.02]"
                          >
                            <td className="px-5 py-4">
                              <div className="flex items-center gap-3">
                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.03] text-slate-300">
                                  <Bot size={17} />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-slate-200">
                                    {agent.name}
                                  </p>
                                  <p className="mt-1 text-[11px] text-slate-500">
                                    {agent.agent_id}
                                  </p>
                                </div>
                              </div>
                            </td>
                            <td className="px-5 py-4 text-xs text-slate-400">
                              {agent.role}
                            </td>
                            <td className="px-5 py-4">
                              <span className="rounded-md border border-white/[0.07] px-2 py-1 text-[10px] text-slate-400">
                                {agent.designation}
                              </span>
                            </td>
                            <td className="px-5 py-4">
                              <StatusBadge status={agent.status} />
                            </td>
                            <td className="px-5 py-4 text-right text-xs tabular-nums text-slate-300">
                              {agent.total_warnings}
                            </td>
                            <td className="px-5 py-4 text-right text-xs tabular-nums text-slate-300">
                              {agent.total_quarantines}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/[0.06] px-5 py-3">
                  <p className="text-[11px] text-slate-500">
                    Agent status and counters are based on the backend response.
                  </p>
                  <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
                    <Activity size={12} />
                    {lastUpdated ? `Updated ${lastUpdated}` : "Not yet updated"}
                  </span>
                </div>
              </section>

              {/* Capability cards */}
              <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-white/[0.07] bg-[#101621] p-5">
                  <div className="flex items-center gap-2 text-cyan-300">
                    <Fingerprint size={18} />
                    <h3 className="text-sm font-medium text-slate-200">
                      Behavioral Fingerprinting
                    </h3>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-slate-500">
                    Behavioral fingerprint data is available through the backend
                    endpoint. Detailed metrics have not been loaded on this
                    overview.
                  </p>
                  <button
                    onClick={() => setActivePage("Behavioral Monitoring")}
                    className="mt-4 flex items-center gap-1.5 text-xs text-cyan-300 hover:text-cyan-200"
                  >
                    Open monitoring <ArrowUpRight size={13} />
                  </button>
                </div>

                <div className="rounded-2xl border border-white/[0.07] bg-[#101621] p-5">
                  <div className="flex items-center gap-2 text-amber-300">
                    <AlertTriangle size={18} />
                    <h3 className="text-sm font-medium text-slate-200">
                      Threat Detection
                    </h3>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-slate-500">
                    Warning total from available agent counters: {warningCount}.
                    Detailed anomaly events are not shown in this overview.
                  </p>
                  <button
                    onClick={() => setActivePage("Threat Detection")}
                    className="mt-4 flex items-center gap-1.5 text-xs text-cyan-300 hover:text-cyan-200"
                  >
                    Open threat detection <ArrowUpRight size={13} />
                  </button>
                </div>

                <div className="rounded-2xl border border-white/[0.07] bg-[#101621] p-5">
                  <div className="flex items-center gap-2 text-emerald-300">
                    <Zap size={18} />
                    <h3 className="text-sm font-medium text-slate-200">
                      Cyber Resilience
                    </h3>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-slate-500">
                    {backupCount} backup-designated agents identified from the
                    current agent list. Failover readiness requires separate
                    verification.
                  </p>
                  <button
                    onClick={() => setActivePage("Cyber Resilience")}
                    className="mt-4 flex items-center gap-1.5 text-xs text-cyan-300 hover:text-cyan-200"
                  >
                    Open resilience <ArrowUpRight size={13} />
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* Other navigation pages */
            <section className="rounded-2xl border border-white/[0.07] bg-[#101621] p-6 sm:p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-cyan-300/15 bg-cyan-300/[0.07] text-cyan-300">
                {(() => {
                  const item = navigation.find(
                    (entry) => entry.label === activePage,
                  );
                  const Icon = item?.icon ?? LayoutDashboard;
                  return <Icon size={23} />;
                })()}
              </div>

              <h2 className="mt-5 text-lg font-semibold text-white">
                {activePage}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                This section is part of the dashboard navigation. Its detailed
                interface has not yet been connected. The current overview
                already retrieves live agent and health data from your backend.
              </p>

              <div className="mt-6 rounded-xl border border-white/[0.06] bg-[#0b1019] p-4">
                <div className="flex items-start gap-3">
                  <CircleAlert
                    size={17}
                    className="mt-0.5 shrink-0 text-amber-300"
                  />
                  <div>
                    <p className="text-sm text-slate-300">
                      Backend integration status
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Agent records loaded: {agents.length}. This page does not
                      execute recovery, quarantine, simulation, or other
                      state-changing operations.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setActivePage("Overview")}
                className="mt-6 rounded-xl border border-cyan-300/20 bg-cyan-300/[0.08] px-4 py-2.5 text-sm text-cyan-200 transition-colors hover:bg-cyan-300/[0.14]"
              >
                Return to Overview
              </button>
            </section>
          )}

          {/* Footer */}
          <footer className="mt-8 flex flex-col justify-between gap-2 border-t border-white/[0.06] pt-5 text-[11px] text-slate-600 sm:flex-row sm:items-center">
            <p>AI-DNA SHIELD · IMMUNO-MAS · Resilience Console</p>
            <p>
              {health?.version
                ? `Backend version ${health.version}`
                : "Backend version not reported"}
              {" · "}
              {backendOnline ? "Service online" : "Service status unverified"}
            </p>
          </footer>
        </div>
      </main>
    </div>
  );
}

export default App;
