<script lang="ts">
  import { createTable, FlexRender, rowSortingFeature, createSortedRowModel, sortFns, tableFeatures, columnFilteringFeature, globalFilteringFeature, createFilteredRowModel, filterFn_includesString, rowPaginationFeature, createPaginatedRowModel, type ColumnDef } from '@tanstack/svelte-table';
  import Eye from '@lucide/svelte/icons/eye';
  import Copy from '@lucide/svelte/icons/copy';
  import Trash2 from '@lucide/svelte/icons/trash-2';
  import * as Pagination from '$lib/components/ui/pagination/index.js';
  import { ScrollArea } from '$lib/components/ui/scroll-area/index.js';
  import DateRangeFilter from '$lib/DateRangeFilter.svelte';
  import type { DateRange } from 'bits-ui';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as ContextMenu from '$lib/components/ui/context-menu/index.js';
  import { notify } from '$lib/notifications';
  import { toast } from 'svelte-sonner';
  import type { Note } from '$lib/api';

  let { notes, onRemove, onSelect }: { notes: Note[]; onRemove: (id: number) => void; onSelect: (note: Note) => void } = $props();
  let range = $state<DateRange | undefined>();
  const filteredNotes = $derived(notes.filter(note => {
    if (!range?.start || !range.end) return true;
    const date = note.created_at?.slice(0, 10);
    return date !== undefined && date >= range.start.toString() && date <= range.end.toString();
  }));
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
    features, columns, get data() { return filteredNotes; },
    globalFilterFn: 'includesString',
    initialState: { pagination: { pageIndex: 0, pageSize: 8 } },
  });
  function setRange(value: DateRange | undefined) {
    range = value;
    table.setPageIndex(0);
  }
</script>

<div class="mb-3 flex flex-wrap items-center gap-2">
<input aria-label="Filter notes" placeholder="Filter notes…" value={table.atoms.globalFilter.get() ?? ''} oninput={(event) => table.setGlobalFilter(event.currentTarget.value)} class="min-w-32 flex-1 rounded-md border bg-background px-3 py-2 text-sm" />
<DateRangeFilter {range} onChange={setRange} />
</div>
<ScrollArea orientation="both" type="always" class="h-[clamp(12rem,calc(100dvh-37rem),20rem)] w-full rounded-md border" aria-label="Notes table scroll area">
  <table class="w-full min-w-72 text-left text-sm">
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
</ScrollArea>
<div class="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
  <span>{table.getPrePaginatedRowModel().rows.length} notes · Page {table.atoms.pagination.get().pageIndex + 1} of {Math.max(1, table.getPageCount())}</span>
  <Pagination.Root count={table.getPrePaginatedRowModel().rows.length} perPage={table.atoms.pagination.get().pageSize} page={table.atoms.pagination.get().pageIndex + 1} onPageChange={(value) => table.setPageIndex(value - 1)} class="mx-0 w-auto">
    {#snippet children({ pages, currentPage })}
      <Pagination.Content>
        <Pagination.Item><Pagination.PrevButton /></Pagination.Item>
        {#each pages as entry (entry.key)}
          <Pagination.Item>
            {#if entry.type === 'ellipsis'}
              <Pagination.Ellipsis />
            {:else}
              <Pagination.Link page={entry} isActive={currentPage === entry.value} size="icon-sm" aria-label={'Page ' + entry.value} />
            {/if}
          </Pagination.Item>
        {/each}
        <Pagination.Item><Pagination.NextButton /></Pagination.Item>
      </Pagination.Content>
    {/snippet}
  </Pagination.Root>
</div>
