<script lang="ts">
  import { createForm } from '@tanstack/svelte-form';
  import { z } from 'zod';
  import { Button } from '$lib/components/ui/button/index.js';
  import { toast } from 'svelte-sonner';

  let { onSave }: { onSave: (text: string) => Promise<void> } = $props();
  const schema = z.object({ text: z.string().trim().min(1, 'Enter a note.').max(2000) });
  let submitting = $state(false);
  const form = createForm(() => ({
    defaultValues: { text: '' },
    validators: { onSubmit: schema },
    onSubmit: async ({ value }) => {
      submitting = true;
      try {
        await onSave(value.text.trim());
        form.reset();
      } catch (error) {
        toast.error(String(error));
      } finally {
        submitting = false;
      }
    },
  }));
</script>

<form novalidate class="mb-4 space-y-2" onsubmit={(event) => {
  event.preventDefault();
  void form.handleSubmit();
}}>
  <form.Field name="text">
    {#snippet children(field)}
      <label for="new-note" class="text-sm font-medium">New note</label>
      <div class="mt-2 flex gap-2">
        <input id="new-note" name={field.name} value={field.state.value}
          onblur={field.handleBlur} oninput={(event) => field.handleChange(event.currentTarget.value)}
          aria-invalid={field.state.meta.errors.length > 0}
          aria-describedby={field.state.meta.errors.length ? 'note-errors' : undefined}
          placeholder="Write a note…" maxlength="2000"
          class="min-w-0 flex-1 rounded-md border bg-background px-3 py-2 text-sm" />
        <Button type="submit" disabled={submitting}>Add note</Button>
      </div>
      {#if field.state.meta.errors.length}
        <p id="note-errors" role="alert" class="text-sm text-destructive">{field.state.meta.errors.map(error => error?.message).join(', ')}</p>
      {/if}
    {/snippet}
  </form.Field>
</form>
