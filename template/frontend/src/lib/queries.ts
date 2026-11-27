import { queryOptions } from '@tanstack/svelte-query';
import { api } from '$lib/api';

export const notesOptions = queryOptions({
  queryKey: ['notes'],
  queryFn: ({ signal }) => api.notes(signal),
});

export const healthOptions = queryOptions({
  queryKey: ['health'],
  queryFn: ({ signal }) => api.health(signal),
  staleTime: 5_000,
});

export const diagnosticsOptions = queryOptions({
  queryKey: ['diagnostics'],
  queryFn: ({ signal }) => api.diagnostics(signal),
  staleTime: 5_000,
});
