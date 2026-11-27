import createClient from 'openapi-fetch';
import type { components, paths } from '$lib/generated/api';

export type Note = components['schemas']['Note'];
export type Health = components['schemas']['Health'];
export type SystemDiagnostics = components['schemas']['Diagnostics'];

export const client = createClient<paths>({ baseUrl: '' });

export const api = {
  async notes(): Promise<Note[]> {
    const { data, response } = await client.GET('/api/notes');
    if (data === undefined) throw new Error('Request failed (' + response.status + ')');
    return data;
  },
  async add(text: string): Promise<Note> {
    const { data, response } = await client.POST('/api/notes', { body: { text } });
    if (data === undefined) throw new Error('Request failed (' + response.status + ')');
    return data;
  },
  async remove(id: number): Promise<void> {
    const { response } = await client.DELETE('/api/notes/{note_id}', {
      params: { path: { note_id: id } },
    });
    if (!response.ok) throw new Error('Request failed (' + response.status + ')');
  },
  async health(): Promise<Health> {
    const { data, error, response } = await client.GET('/api/health');
    if (data !== undefined) return data;
    if (response.status === 503 && error !== undefined) return error;
    throw new Error('Health check failed (' + response.status + ')');
  },
  async diagnostics(): Promise<SystemDiagnostics> {
    const { data, response } = await client.GET('/api/diagnostics');
    if (data === undefined) throw new Error('Request failed (' + response.status + ')');
    return data;
  },
};
