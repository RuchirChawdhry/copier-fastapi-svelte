import createClient from 'openapi-fetch';
import type { components, paths } from '$lib/generated/api';

export type Note = components['schemas']['Note'];
export type Health = components['schemas']['Health'];
export type SystemDiagnostics = components['schemas']['Diagnostics'];

export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
  }
}

export const client = createClient<paths>({
  baseUrl: '',
  fetch: async (request) => {
    try {
      return await fetch(request);
    } catch (error) {
      if (request.signal.aborted) throw error;
      throw new ApiError('Cannot reach the API. Check your connection or run task doctor.');
    }
  },
});

function detailOf(error: unknown): string | undefined {
  if (!error || typeof error !== 'object' || !('detail' in error)) return;
  const detail = error.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((issue: unknown) => {
      if (!issue || typeof issue !== 'object' || !('msg' in issue) || typeof issue.msg !== 'string') return '';
      const field = 'loc' in issue && Array.isArray(issue.loc) ? issue.loc.slice(1).join('.') : '';
      return field ? field + ': ' + issue.msg : issue.msg;
    }).filter(Boolean).join('; ') || undefined;
  }
}

function fail(operation: string, response: Response, error: unknown): never {
  const status = response.status;
  const messages: Record<number, string> = {
    401: 'Sign in and try again.',
    403: 'You do not have permission.',
    404: 'The requested resource no longer exists.',
    409: 'The data has changed. Refresh and try again.',
    422: 'Check the submitted values.',
    429: 'Too many requests. Try again shortly.',
    502: 'The API is not reachable. Check the backend service.',
    503: 'The service is unavailable. Check its dependencies.',
    504: 'The API timed out. Try again.',
  };
  const detail = status >= 400 && status < 500 && ![401, 403, 429].includes(status) ? detailOf(error) : undefined;
  const explanation = detail ?? messages[status] ?? (status >= 500 ? 'The server encountered an error.' : 'Unexpected API response.');
  throw new ApiError(operation + ': ' + explanation + ' (HTTP ' + status + ')', status);
}

export const api = {
  async notes(signal?: AbortSignal): Promise<Note[]> {
    const { data, error, response } = await client.GET('/api/notes', { signal });
    if (data === undefined) fail('Could not load notes', response, error);
    return data;
  },
  async add(text: string): Promise<Note> {
    const { data, error, response } = await client.POST('/api/notes', { body: { text } });
    if (data === undefined) fail('Could not save note', response, error);
    return data;
  },
  async remove(id: number): Promise<void> {
    const { error, response } = await client.DELETE('/api/notes/{note_id}', {
      params: { path: { note_id: id } },
    });
    if (!response.ok) fail('Could not delete note ' + id, response, error);
  },
  async health(signal?: AbortSignal): Promise<Health> {
    const { data, error, response } = await client.GET('/api/health', { signal });
    if (data !== undefined) return data;
    if (response.status === 503 && error !== undefined) return error;
    fail('Could not check service health', response, error);
  },
  async diagnostics(signal?: AbortSignal): Promise<SystemDiagnostics> {
    const { data, error, response } = await client.GET('/api/diagnostics', { signal });
    if (data === undefined) fail('Could not load system diagnostics', response, error);
    return data;
  },
};
