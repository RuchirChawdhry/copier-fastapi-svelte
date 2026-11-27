<script lang="ts">
  import { today } from '@internationalized/date';
  import type { DateRange } from 'bits-ui';
  import CalendarDays from '@lucide/svelte/icons/calendar-days';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { RangeCalendar } from '$lib/components/ui/range-calendar/index.js';

  let { range, onChange }: { range: DateRange | undefined; onChange: (value: DateRange | undefined) => void } = $props();
  let open = $state(false);
  let draft = $state<DateRange | undefined>();
  const now = today('UTC');

  function apply(value: DateRange | undefined) {
    onChange(value);
    open = false;
  }
</script>

<Popover.Root bind:open onOpenChange={(value) => { if (value) draft = range; }}>
  <Popover.Trigger>
    {#snippet child({ props })}
      <Button {...props} variant="outline" aria-label="Filter by creation date">
        <CalendarDays aria-hidden="true" />
        {range?.start && range.end ? range.start.toString() + ' – ' + range.end.toString() : 'Any date'}
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content side="right" align="center" collisionPadding={12} class="w-80 max-w-[calc(100vw-1.5rem)] max-h-[var(--bits-popover-content-available-height)] overflow-y-auto p-3">
    <Popover.Header>
      <Popover.Title>Creation date</Popover.Title>
      <Popover.Description>Filter notes by date (UTC). Undated notes appear only with no date filter.</Popover.Description>
    </Popover.Header>
    <div class="my-2 flex flex-wrap gap-2">
      <Button size="sm" variant="outline" onclick={() => draft = { start: now.subtract({ days: 6 }), end: now }}>Last 7 days</Button>
      <Button size="sm" variant="outline" onclick={() => draft = { start: now.set({ day: 1 }).subtract({ months: 1 }), end: now.set({ day: 1 }).subtract({ days: 1 }) }}>Previous month</Button>
    </div>
    <RangeCalendar bind:value={draft} maxValue={now} calendarLabel="Note creation dates" class="mx-auto !p-1" />
    <div class="flex justify-between gap-2 border-t pt-3">
      <Button variant="ghost" onclick={() => apply(undefined)}>Clear filter</Button>
      <Button disabled={!draft?.start || !draft.end} onclick={() => apply(draft)}>Apply range</Button>
    </div>
  </Popover.Content>
</Popover.Root>
