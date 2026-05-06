import type { DashboardData, SystemStatus } from "../types/api";

export const API_BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export const api = {
  systemStatus: () => j<SystemStatus>("/system-status"),
  dashboardData: () => j<DashboardData>("/dashboard-data"),
  tradeLogs: () => j<{ trades: any[] }>("/trade-logs"),
  availableAssets: () => j<{ assets: string[] }>("/available-assets"),
  resetSimulation: () =>
    j<{ ok: boolean }>("/reset-simulation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}"
    }),
  uploadDataset: async (args: { file: File; target_name: string; dataset_type: "market" | "macro" }) => {
    const form = new FormData();
    form.append("file", args.file);
    const res = await fetch(
      `${API_BASE}/upload-dataset?dataset_type=${encodeURIComponent(args.dataset_type)}&target_name=${encodeURIComponent(
        args.target_name
      )}`,
      { method: "POST", body: form }
    );
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return (await res.json()) as { ok: boolean; filename: string; dataset_type: string };
  },
  startSimulation: (body: { action: string; ticker?: string; speed?: number }) =>
    j<{ ok: boolean; simulation: any }>("/start-simulation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })
};

