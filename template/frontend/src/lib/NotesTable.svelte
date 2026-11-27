<script lang="ts">
  import { createTable, FlexRender, rowSortingFeature, createSortedRowModel, sortFns, tableFeatures, columnFilteringFeature, globalFilteringFeature, createFilteredRowModel, filterFn_includesString, rowPaginationFeature, createPaginatedRowModel, type ColumnDef } from '@tanstack/svelte-table';
  import Eye from '@lucide/svelte/icons/eye';
  import Copy from '@lucide/svelte/icons/copy';
  import Trash2 from '@lucide/svelte/icons/trash-2';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as ContextMenu from '$lib/components/ui/context-menu/index.js';
  import { notify } from '$lib/notifications';
  import { toast } from 'svelte-sonner';
  import type { Note } from '$lib/api';

  let { notes, onRemove, onSelect }: { notes: Note[]; onRemove: (id: number) => void; onSelect: (note: Note) => void } = $props();
  const features = tableFeatures({
    columnFilteringFeature, globalFilteringFeature,
    filteredRowModel: createFilteredRowModel(),
    filterFns: { includesString: filterFn_includesString },
    rowSortingFeature, sortedRowModel: createSortedRowModel(), sortFns,
    rowPaginationFeature, paginatedRowModel: createPaginatedRowModel(),
  });
  const columns: ColumnDef<typeof features, Note>[] = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'text', header: 'Note' },
  ];
  const table = createTable({
    features, columns, get data() { return notes; },
    globalFilterFn: 'includesString',
    initialState: { pagination: { pageIndex: 0, pageSize: 8 } },
  });
</script>

<input aria-label="Filter notes" placeholder="Filter notes…" value={table.atoms.globalFilter.get() ?? ''} oninput={(event) => table.setGlobalFilter(event.currentTarget.value)} class="mb-3 w-full rounded-md border bg-background px-3 py-2 text-sm" />
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
      {#each table.getRowModel().rows as row (row.original.id)}
        <tr class="border-t hover:bg-muted/40">
          <td class="px-3 py-2 font-mono text-xs text-muted-foreground">{row.original.id}</td>
          <td class="px-3 py-2">
            <ContextMenu.Root>
              <ContextMenu.Trigger>
                <button class="text-left break-all" onclick={() => onSelect(row.original)}>{row.original.text}</button>
              </ContextMenu.Trigger>
              <ContextMenu.Content>
                <ContextMenu.Item onSelect={() => onSelect(row.original)}><Eye aria-hidden="true" class="size-4 shrink-0" /> View details</ContextMenu.Item>
                <ContextMenu.Item onSelect={() => navigator.clipboard.writeText(row.original.text).then(() => notify('Copied'), () => toast.error('Clipboard unavailable'))}><Copy aria-hidden="true" class="size-4 shrink-0" /> Copy note</ContextMenu.Item>
                <ContextMenu.Item onSelect={() => onRemove(row.original.id)} class="text-destructive"><Trash2 aria-hidden="true" class="size-4 shrink-0" /> Delete note</ContextMenu.Item>
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
  <span>{table.getPrePaginatedRowModel().rows.length} notes · Page {table.atoms.pagination.get().pageIndex + 1} of {Math.max(1, table.getPageCount())}</span>
  <div class="flex gap-1">
    <Button size="sm" variant="outline" disabled={!table.getCanPreviousPage()} onclick={() => table.previousPage()}>Previous</Button>
    <Button size="sm" variant="outline" disabled={!table.getCanNextPage()} onclick={() => table.nextPage()}>Next</Button>
  </div>
</div>

