<script lang="ts">
  import type { Note } from '$lib/api';
  import * as Marker from '$lib/components/ui/marker/index.js';

  let { selected }: { selected: Note | undefined } = $props();
</script>

<div class="pl-4">
  <Marker.Root variant="separator" class="mb-4">
    <Marker.Content>Note details</Marker.Content>
  </Marker.Root>
  {#if selected}
    <p class="mb-2 font-mono text-xs text-muted-foreground">ID {selected.id}</p>
    <p class="break-all text-sm">{selected.text}</p>
    <p class="mt-3 text-xs text-muted-foreground">Created: {selected.created_at ? selected.created_at.slice(0, 10) + ' UTC' : 'Unknown'}</p>
  {:else}
    <p class="text-sm text-muted-foreground">Select a note to inspect it.</p>
  {/if}
</div>
