import type { Agent, HealthResponse } from "../types";

export const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function fetchJSON<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`);

  if (!response.ok) {
    throw new Error(
      `Backend request failed: ${endpoint} (HTTP ${response.status})`,
    );
  }

  return (await response.json()) as T;
}

export async function getAgents(): Promise<Agent[]> {
  const data = await fetchJSON<unknown>("/agents");

  let records: unknown[] = [];

  if (Array.isArray(data)) {
    records = data;
  } else if (data && typeof data === "object") {
    const object = data as Record<string, unknown>;

    if (Array.isArray(object.agents)) {
      records = object.agents;
    } else if (Array.isArray(object.data)) {
      records = object.data;
    }
  }

  if (records.length === 0) {
    throw new Error(
      "No agent records found in the /agents response. Check the API response.",
    );
  }

  return records.map((item, index): Agent => {
    const record = item as Record<string, unknown>;

    const agentId = String(
      record.agent_id ?? record.agentId ?? record.id ?? `AGENT-${index + 1}`,
    );

    const rawStatus = String(
      record.status ?? record.raw_status ?? record.state ?? "UNKNOWN",
    );

    const status = rawStatus.toUpperCase();

    return {
      id: agentId,
      agent_id: agentId,
      name: String(record.name ?? agentId),
      role: String(record.role ?? ""),
      status: rawStatus,
      raw_status: String(record.raw_status ?? rawStatus),
      designation: String(record.designation ?? ""),
      warn_count: Number(record.warn_count ?? record.total_warnings ?? 0),
      total_warnings: Number(record.total_warnings ?? record.warn_count ?? 0),
      total_quarantines: Number(record.total_quarantines ?? 0),
      is_active_backup: Boolean(record.is_active_backup ?? false),
      available:
        typeof record.available === "boolean"
          ? record.available
          : ["HEALTHY", "ACTIVE", "ONLINE", "STANDBY"].includes(status),
    };
  });
}

export function getHealth(): Promise<HealthResponse> {
  return fetchJSON<HealthResponse>("/health");
}
