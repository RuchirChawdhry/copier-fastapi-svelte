<script lang="ts">
  import * as Select from '$lib/components/ui/select/index.js';
  import { themes, type Theme } from '$lib/theme';
  import { themeIcons } from './theme-icons';

  let { theme, setTheme }: { theme: Theme; setTheme: (theme: Theme) => void } = $props();
</script>

<section class="rounded-lg border bg-card p-5">
  <h2 class="text-lg font-semibold">Appearance</h2>
  <p class="mb-4 text-sm text-muted-foreground">Theme preference is saved on this browser.</p>
  <div class="flex items-center justify-between gap-4">
    <div>
      <label for="theme-select" class="font-medium">Color theme</label>
      <p class="mt-1 text-sm text-muted-foreground">Choose one of five application themes.</p>
    </div>
    <Select.Root type="single" value={theme} onValueChange={(value) => setTheme(value as Theme)}>
      <Select.Trigger id="theme-select" aria-label="Color theme" class="min-w-48">{themes.find(option => option.id === theme)?.label}</Select.Trigger>
      <Select.Content>
        {#each themes as option (option.id)}
          {@const Icon = themeIcons[option.id]}
          <Select.Item value={option.id} label={option.label}><Icon class="size-4" aria-hidden="true" /> {option.label}</Select.Item>
        {/each}
      </Select.Content>
    </Select.Root>
  </div>
</section>
