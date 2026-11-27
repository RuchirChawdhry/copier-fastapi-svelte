export type Note = { id: number; text: string };
export type Health = { status: string; dependencies: Record<string, string> };

export type SystemDiagnostics = {
  cpu_percent: number; logical_cpus: number | null;
  memory_used_bytes: number; memory_total_bytes: number;
  disk_used_bytes: number; disk_total_bytes: number;
  process_rss_bytes: number; uptime_seconds: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch('/api' + path, init);
  if (!response.ok) throw new Error('Request failed (' + response.status + ')');
  return response.status === 204 ? undefined as T : await response.json() as T;
}

export const api = {
  diagnostics: () => request<SystemDiagnostics>('/diagnostics'),
  notes: () => request<Note[]>('/notes'),
  add: (text: string) => request<Note>('/notes', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }),
  }),
  remove: (id: number) => request<void>('/notes/' + id, { method: 'DELETE' }),
  health: async (): Promise<Health> => {
    const response = await fetch('/api/health');
    if (![200, 503].includes(response.status)) throw new Error('Health check failed');
    return response.json();
  },
};

