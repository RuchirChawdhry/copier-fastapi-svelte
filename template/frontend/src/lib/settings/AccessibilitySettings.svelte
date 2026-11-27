<script lang="ts">
  import Accessibility from '@lucide/svelte/icons/accessibility';
  import { Switch } from '$lib/components/ui/switch/index.js';
  import * as Item from '$lib/components/ui/item/index.js';
  import { preferences, setPreference } from '$lib/preferences.svelte';
</script>

<section class="rounded-lg border bg-card p-5">
  <h2 class="flex items-center gap-2 text-lg font-semibold"><Accessibility class="size-5" aria-hidden="true" /> Accessibility</h2>
  <Item.Root class="px-0">
    <Item.Content>
      <label for="reduced-motion" class="font-medium">Reduce motion</label>
      <Item.Description id="motion-description">Minimize transitions, animations and smooth scrolling.</Item.Description>
    </Item.Content>
    <Item.Actions><Switch id="reduced-motion" aria-describedby="motion-description" checked={preferences.reducedMotion} onCheckedChange={(value) => setPreference('reducedMotion', value)} /></Item.Actions>
  </Item.Root>
</section>
