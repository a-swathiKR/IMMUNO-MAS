
import {
  Activity,
  Shield,
  LayoutDashboard,
  Bot,
  Fingerprint,
  AlertTriangle,
  RefreshCw,
  ShieldCheck,
  ScrollText,
  Settings,
  GitBranch,
} from "lucide-react";

export type PageId =
  | "overview"
  | "agents"
  | "behavior"
  | "threats"
  | "resilience"
  | "failover"
  | "audit"
  | "settings";

interface SidebarProps {
  activePage: PageId;
  onPageChange: (page: PageId) => void;
}

const navigation = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "agents", label: "Agent Management", icon: Bot },
  { id: "behavior", label: "Behavioral Monitoring", icon: Fingerprint },
  { id: "threats", label: "Threat Detection", icon: AlertTriangle },
  { id: "resilience", label: "Cyber Resilience", icon: ShieldCheck },
  { id: "failover", label: "Failover & Recovery", icon: RefreshCw },
  { id: "audit", label: "Audit Logs", icon: ScrollText },
  { id: "settings", label: "Settings", icon: Settings },
] satisfies {
  id: PageId;
  label: string;
  icon: typeof LayoutDashboard;
}[];

export default function Sidebar({
  activePage,
  onPageChange,
}: SidebarProps) {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex h-screen w-64 flex-col overflow-y-auto border-r border-[#263244] bg-[#0D111B]">
      <div className="flex h-[76px] shrink-0 items-center gap-3 border-b border-[#263244] px-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sky-400/10 text-sky-400">
          <Shield size={23} />
        </div>

        <div className="min-w-0">
          <div className="text-sm font-bold tracking-wide text-slate-100">
            IMMUNO-MAS
          </div>
          <div className="mt-1 text-[10px] tracking-[0.2em] text-slate-500">
            AI-DNA SHIELD
          </div>
        </div>
      </div>

      <div className="px-4 pb-2 pt-6 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        Security Console
      </div>

      <nav className="flex-1 space-y-1 px-3 pb-4">
        {navigation.map(({ id, label, icon: Icon }) => {
          const isActive = activePage === id;

          return (
            <button
              key={id}
              type="button"
              onClick={() => onPageChange(id)}
              aria-current={isActive ? "page" : undefined}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 text-left text-sm transition-colors ${
                isActive
                  ? "border border-sky-400/20 bg-sky-400/10 text-sky-300"
                  : "border border-transparent text-slate-400 hover:bg-white/[0.04] hover:text-slate-100"
              }`}
            >
              <Icon size={18} className="shrink-0" />
              <span className="min-w-0">{label}</span>
            </button>
          );
        })}
      </nav>

      <div className="shrink-0 border-t border-[#263244] p-4">
        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/[0.05] p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-400">
            <Activity size={15} />
            Resilience Framework
          </div>
          <p className="mt-2 text-[11px] leading-5 text-slate-500">
            Behavioral fingerprinting and autonomous recovery
          </p>
          <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-500">
            <GitBranch size={12} />
            AI-DNA SHIELD v2.0
          </div>
        </div>
      </div>
    </aside>
  );
}
