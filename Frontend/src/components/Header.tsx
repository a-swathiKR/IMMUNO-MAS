import { Bell, ShieldCheck } from "lucide-react";
import type { PageId } from "./Sidebar";

interface HeaderProps {
  activePage: PageId;
  backendOnline: boolean;
}

const pageTitles: Record<PageId, string> = {
  overview: "Overview",
  agents: "Agent Management",
  behavior: "Behavioral Monitoring",
  threats: "Threat Detection",
  resilience: "Cyber Resilience",
  failover: "Failover & Recovery",
  audit: "Audit Logs",
  settings: "Settings",
};

export default function Header({ activePage, backendOnline }: HeaderProps) {
  return (
    <header className="flex min-h-20 items-center justify-between gap-4 border-b border-slate-800 bg-[#0b101a]/90 px-5 py-4 md:px-8">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">
          {pageTitles[activePage]}
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          IMMUNO-MAS / Security Console
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div
          className={`flex items-center gap-2 rounded-full border px-3 py-2 text-xs ${
            backendOnline
              ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
              : "border-red-500/20 bg-red-500/10 text-red-400"
          }`}
        >
          <ShieldCheck size={15} />
          <span>{backendOnline ? "Backend Online" : "Backend Offline"}</span>
        </div>

        <button
          type="button"
          aria-label="Notifications"
          title="Notifications"
          className="rounded-lg border border-slate-800 p-2.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
        >
          <Bell size={17} />
        </button>
      </div>
    </header>
  );
}
