<script lang="ts">
  import Bell from '@lucide/svelte/icons/bell';
  import MessageSquare from '@lucide/svelte/icons/message-square';
  import Monitor from '@lucide/svelte/icons/monitor';
  import { Switch } from '$lib/components/ui/switch/index.js';
  import { Separator } from '$lib/components/ui/separator/index.js';
  import * as Item from '$lib/components/ui/item/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { toast } from 'svelte-sonner';
  import { preferences, setPreference } from '$lib/preferences.svelte';
  import { requestNotifications } from '$lib/notifications';
</script>

<section class="rounded-lg border bg-card p-5">
  <h2 class="flex items-center gap-2 text-lg font-semibold"><Bell class="size-5" aria-hidden="true" /> Notifications</h2>
  <p class="mb-4 text-sm text-muted-foreground">Control which notifications this browser displays.</p>
  <Item.Root class="px-0">
    <Item.Content>
      <label for="success-toasts" class="flex items-center gap-2 font-medium"><MessageSquare class="size-4" aria-hidden="true" /> Success notifications</label>
      <Item.Description id="success-description">Show a toast when an operation succeeds. Errors always remain visible.</Item.Description>
    </Item.Content>
    <Item.Actions><Switch id="success-toasts" aria-describedby="success-description" checked={preferences.successToasts} onCheckedChange={(value) => setPreference('successToasts', value)} /></Item.Actions>
  </Item.Root>
  <Separator />
  <Item.Root class="px-0">
    <Item.Content>
      <label for="desktop-notifications" class="flex items-center gap-2 font-medium"><Monitor class="size-4" aria-hidden="true" /> Desktop notifications</label>
      <Item.Description id="desktop-description">Allow browser notifications while the application is open, subject to browser permission.</Item.Description>
    </Item.Content>
    <Item.Actions><Switch id="desktop-notifications" aria-describedby="desktop-description" checked={preferences.desktopNotifications} onCheckedChange={(value) => value ? void requestNotifications() : setPreference('desktopNotifications', false)} /></Item.Actions>
  </Item.Root>
  <Button variant="outline" onclick={() => { toast.success('Notification test'); if (preferences.desktopNotifications && 'Notification' in window && Notification.permission === 'granted') new Notification('Notification test'); }}><Bell class="size-4" aria-hidden="true" /> Test notification</Button>
</section>
