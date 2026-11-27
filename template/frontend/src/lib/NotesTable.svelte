<script lang="ts">
  import { createTable, FlexRender, rowSortingFeature, createSortedRowModel, sortFns, tableFeatures, type ColumnDef } from '@tanstack/svelte-table';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as ContextMenu from '$lib/components/ui/context-menu/index.js';
  import { notify } from '$lib/notifications';
  import { toast } from 'svelte-sonner';
  import type { Note } from '$lib/api';

  let { notes, onRemove, onSelect }: { notes: Note[]; onRemove: (id: number) => void; onSelect: (note: Note) => void } = $props();
  let search = $state('');
  let page = $state(0);
  const pageSize = 8;
  let filtered = $derived(notes.filter(note => note.text.toLowerCase().includes(search.toLowerCase())));
  const columns: ColumnDef<Note>[] = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'text', header: 'Note' },
  ];
  const features = tableFeatures({ rowSortingFeature, sortedRowModel: createSortedRowModel(), sortFns });
  const table = createTable({ features, columns, get data() { return filtered; } });
  let rows = $derived(table.getRowModel().rows);
  let lastPage = $derived(Math.max(0, Math.ceil(rows.length / pageSize) - 1));
  let activePage = $derived(Math.min(page, lastPage));
</script>

<input aria-label="Filter notes" placeholder="Filter notes…" bind:value={search} oninput={() => page = 0} class="mb-3 w-full rounded-md border bg-background px-3 py-2 text-sm" />
<div class="overflow-x-auto rounded-md border">
  <table class="w-full text-left text-sm">
    <thead class="bg-muted text-muted-foreground">
      {#each table.getHeaderGroups() as group (group.id)}
        <tr>
          {#each group.headers as header (header.id)}
            <th class="px-3 py-2" aria-sort={header.column.getIsSorted() === 'asc' ? 'ascending' : header.column.getIsSorted() === 'desc' ? 'descending' : 'none'}>
              <button onclick={header.column.getToggleSortingHandler()}><FlexRender {header} /> {header.column.getIsSorted() === 'asc' ? '↑' : header.column.getIsSorted() === 'desc' ? '↓' : '↕'}</button>
            </th>
          {/each}
          <th class="px-3 py-2">Actions</th>
        </tr>
      {/each}
    </thead>
    <tbody>
      {#each rows.slice(activePage * pageSize, (activePage + 1) * pageSize) as row (row.original.id)}
        <tr class="border-t hover:bg-muted/40">
          <td class="px-3 py-2 font-mono text-xs text-muted-foreground">{row.original.id}</td>
          <td class="px-3 py-2">
            <ContextMenu.Root>
              <ContextMenu.Trigger>
                <button class="text-left break-all" onclick={() => onSelect(row.original)}>{row.original.text}</button>
              </ContextMenu.Trigger>
              <ContextMenu.Content>
                <ContextMenu.Item onSelect={() => onSelect(row.original)}>View details</ContextMenu.Item>
                <ContextMenu.Item onSelect={() => navigator.clipboard.writeText(row.original.text).then(() => notify('Copied'), () => toast.error('Clipboard unavailable'))}>Copy note</ContextMenu.Item>
                <ContextMenu.Item onSelect={() => onRemove(row.original.id)}>Delete note</ContextMenu.Item>
              </ContextMenu.Content>
            </ContextMenu.Root>
          </td>
          <td class="px-3 py-2"><Button size="sm" variant="ghost" onclick={() => onRemove(row.original.id)}>Delete</Button></td>
        </tr>
      {:else}
        <tr><td colspan="3" class="p-6 text-center text-muted-foreground">No notes found.</td></tr>
      {/each}
    </tbody>
  </table>
</div>
<div class="mt-3 flex items-center justify-between gap-2 text-xs text-muted-foreground">
  <span>{rows.length} notes · Page {activePage + 1} of {lastPage + 1}</span>
  <div class="flex gap-1">
    <Button size="sm" variant="outline" disabled={activePage === 0} onclick={() => page = activePage - 1}>Previous</Button>
    <Button size="sm" variant="outline" disabled={activePage >= lastPage} onclick={() => page = activePage + 1}>Next</Button>
  </div>
</div>

