<script lang="ts">
  import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
  import App from './App.svelte';

  const client = new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1 },
    },
  });
</script>

<QueryClientProvider {client}>
  <App />
</QueryClientProvider>
