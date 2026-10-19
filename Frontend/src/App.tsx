
import { useCallback, useEffect, useState } from "react";

import Sidebar, { type PageId } from "./components/Sidebar";
import Header from "./components/Header";

import Overview from "./pages/Overview";
import AgentManagement from "./pages/AgentManagement";
import BehavioralMonitoring from "./pages/BehavioralMonitoring";
import ThreatDetection from "./pages/ThreatDetection";
import CyberResilience from "./pages/CyberResilience";
import FailoverRecovery from "./pages/FailoverRecovery";
import AuditLogs from "./pages/AuditLogs";
import Settings from "./pages/Settings";

import { API_BASE, getAgents, getHealth } from "./services/api";
import type { Agent, HealthResponse } from "./types";

type JsonObject = Record<string, unknown>;

async function fetchOptional<T>(
  endpoint: string,
  fallback: T
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`);

    if (!response.ok) {
      return fallback;
    }

    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

function extractArray(
  value: unknown,
  keys: string[] = []
): unknown[] {
  if (Array.isArray(value)) {
    return value;
  }

  if (value && typeof value === "object") {
    const object = value as JsonObject;

    for (const key of keys) {
      if (Array.isArray(object[key])) {
        return object[key] as unknown[];
      }
    }
  }

  return [];
}

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("overview");

  const [agents, setAgents] = useState<Agent[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [logs, setLogs] = useState<unknown[]>([]);
  const [anomalies, setAnomalies] = useState<unknown[]>([]);
  const [fingerprints, setFingerprints] = useState<unknown[]>([]);
  const [resilienceStatus, setResilienceStatus] = useState<unknown>(null);
  const [resilienceEvents, setResilienceEvents] = useState<unknown[]>([]);
  const [settings, setSettings] = useState<unknown>(null);

  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);

  const loadBackendData = useCallback(async () => {
    setLoading(true);
    setApiError(null);

    try {
      const [agentData, healthData] = await Promise.all([
        getAgents(),
        getHealth(),
      ]);

      setAgents(agentData);
      setHealth(healthData);

      const [
        logData,
        anomalyData,
        fingerprintData,
        resilienceData,
        eventData,
        settingsData,
      ] = await Promise.all([
        fetchOptional<unknown>("/behavior/logs", []),
        fetchOptional<unknown>("/behavior/anomalies", []),
        fetchOptional<unknown>("/behavior/fingerprints", []),
        fetchOptional<unknown>("/resilience/status", null),
        fetchOptional<unknown>("/resilience/events", []),
        fetchOptional<unknown>("/settings", null),
      ]);

      setLogs(extractArray(logData, ["logs", "events", "data"]));
      setAnomalies(extractArray(anomalyData, ["anomalies", "data"]));
      setFingerprints(
        extractArray(fingerprintData, ["fingerprints", "data"])
      );
      setResilienceStatus(resilienceData);
      setResilienceEvents(
        extractArray(eventData, ["events", "resilience_events", "data"])
      );
      setSettings(settingsData);
    } catch (error) {
      setApiError(
        error instanceof Error
          ? error.message
          : "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBackendData();
  }, [loadBackendData]);

  const backendOnline = health !== null && apiError === null;

  function renderPage() {
    switch (activePage) {
      case "overview":
        return (
          <Overview
            agents={agents}
            backendOnline={backendOnline}
          />
        );

      case "agents":
        return (
          <AgentManagement
            agents={agents}
            loading={loading}
            error={apiError}
          />
        );

      case "behavior":
        return (
          <BehavioralMonitoring
            logs={logs}
            anomalies={anomalies}
            fingerprints={fingerprints}
            loading={loading}
            error={apiError}
          />
        );

      case "threats":
        return (
          <ThreatDetection
            anomalies={anomalies}
            loading={loading}
            error={apiError}
          />
        );

      case "resilience":
        return (
          <CyberResilience
            resilienceStatus={resilienceStatus}
            backendOnline={backendOnline}
            loading={loading}
            error={apiError}
          />
        );

      case "failover":
        return (
          <FailoverRecovery
            resilienceStatus={resilienceStatus}
            events={resilienceEvents}
            loading={loading}
            error={apiError}
          />
        );

      case "audit":
        return (
          <AuditLogs
            logs={logs}
            loading={loading}
            error={apiError}
          />
        );

      case "settings":
        return (
          <Settings
            settings={settings}
            loading={loading}
            error={apiError}
          />
        );
    }
  }

  return (
    <div className="min-h-screen bg-[#080B12] text-slate-100">
      <Sidebar
        activePage={activePage}
        onPageChange={setActivePage}
      />

      <div className="min-h-screen min-w-0 md:ml-64">
        <Header
          activePage={activePage}
          backendOnline={backendOnline}
        />

        <main className="min-w-0 px-4 pb-6 pt-3 sm:px-6 lg:px-8">
          {apiError && (
            <div
              role="alert"
              className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300"
            >
              <span>Backend connection issue: {apiError}</span>
              <button
                type="button"
                onClick={() => void loadBackendData()}
                className="underline underline-offset-4"
              >
                Retry
              </button>
            </div>
          )}

          {renderPage()}

          <footer className="mt-6 border-t border-slate-800 pt-3 text-xs text-slate-500">
            AI-DNA SHIELD · Autonomous Multi-Agent Cyber Resilience
          </footer>
        </main>
      </div>
    </div>
  );
}
