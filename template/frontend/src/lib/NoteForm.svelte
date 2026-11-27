<script lang="ts">
  import { Control, Field, FieldErrors, Label } from 'formsnap';
  import { defaults, superForm, setError } from 'sveltekit-superforms';
  import { zod } from 'sveltekit-superforms/adapters';
  import { z } from 'zod';
  import { Button } from '$lib/components/ui/button/index.js';

  let { onSave }: { onSave: (text: string) => Promise<void> } = $props();
  const schema = z.object({ text: z.string().trim().min(1, 'Enter a note.').max(2000) });
  const form = superForm(defaults({ text: '' }, zod(schema)), {
    SPA: true,
    validators: zod(schema),
    resetForm: false,
    async onUpdate({ form: result }) {
      if (!result.valid) return;
      try {
        await onSave(result.data.text);
        result.data.text = '';
      } catch (error) {
        setError(result, 'text', String(error));
      }
    },
  });
  const { form: data, enhance, submitting } = form;
</script>

<form method="POST" use:enhance novalidate class="mb-4 space-y-2">
  <Field {form} name="text">
    <Control>
      {#snippet children({ props })}
        <Label class="text-sm font-medium">New note</Label>
        <div class="mt-2 flex gap-2">
          <input {...props} placeholder="Write a note…" maxlength="2000" bind:value={$data.text} class="min-w-0 flex-1 rounded-md border bg-background px-3 py-2 text-sm" />
          <Button type="submit" disabled={$submitting}>Add note</Button>
        </div>
      {/snippet}
    </Control>
    <FieldErrors class="text-sm text-destructive" />
  </Field>
</form>

