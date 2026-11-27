<script lang="ts">
  import { createQuery } from '@tanstack/svelte-query';
  import { diagnosticsOptions } from '$lib/queries';
  import { Button } from '$lib/components/ui/button/index.js';
  const query = createQuery(() => diagnosticsOptions);
  const data = $derived(query.data);
  const gib = (value: number) => (value / 1073741824).toFixed(2) + ' GiB';
</script>

<section class="space-y-5">
  <div class="flex items-center justify-between"><div><h1 class="text-3xl font-semibold tracking-tight">System diagnostics</h1><p class="mt-1 text-sm text-muted-foreground">Live metrics from the backend host.</p></div><Button variant="outline" onclick={() => query.refetch()} disabled={query.isFetching}>Refresh metrics</Button></div>
  {#if data}
    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {#each [{ label: 'CPU', percent: data.cpu_percent, detail: data.logical_cpus + ' logical CPUs' }, { label: 'Memory', percent: 100 * data.memory_used_bytes / data.memory_total_bytes, detail: gib(data.memory_used_bytes) + ' / ' + gib(data.memory_total_bytes) }, { label: 'Disk', percent: 100 * data.disk_used_bytes / data.disk_total_bytes, detail: gib(data.disk_used_bytes) + ' / ' + gib(data.disk_total_bytes) }] as metric (metric.label)}
        <div class="rounded-lg border bg-card p-5">
          <p class="text-sm text-muted-foreground">{metric.label}</p>
          <p class="mt-2 text-2xl font-semibold">{metric.percent.toFixed(1)}%</p>
          <div class="my-3 h-2 overflow-hidden rounded-full bg-muted"><div class="h-full rounded-full bg-primary" style:width={metric.percent + '%'}></div></div>
          <p class="text-xs text-muted-foreground">{metric.detail}</p>
        </div>
      {/each}
      <div class="rounded-lg border bg-card p-5"><p class="text-sm text-muted-foreground">API process RAM (RSS)</p><p class="mt-2 text-2xl font-semibold">{(data.process_rss_bytes / 1048576).toFixed(1)} MiB</p></div>
      <div class="rounded-lg border bg-card p-5"><p class="text-sm text-muted-foreground">Host uptime</p><p class="mt-2 text-2xl font-semibold">{Math.floor(data.uptime_seconds / 3600)} h</p></div>
    </div>
  {:else if query.isError}
    <p role="alert" class="text-destructive">{query.error.message}</p>
  {:else}
    <p class="text-muted-foreground">Loading metrics…</p>
  {/if}
</section>

