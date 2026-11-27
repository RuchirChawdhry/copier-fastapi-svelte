<script lang="ts">
  import type { Theme } from '$lib/theme';
  import AppearanceSettings from '$lib/settings/AppearanceSettings.svelte';
  import NotificationSettings from '$lib/settings/NotificationSettings.svelte';
  import AccessibilitySettings from '$lib/settings/AccessibilitySettings.svelte';

  let { theme, setTheme }: { theme: Theme; setTheme: (theme: Theme) => void } = $props();
</script>

<h1 class="text-3xl font-semibold tracking-tight">Settings</h1>
<AppearanceSettings {theme} {setTheme} />
<NotificationSettings />
<AccessibilitySettings />
