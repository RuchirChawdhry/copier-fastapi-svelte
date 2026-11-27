import { toast } from 'svelte-sonner';
import { preferences, setPreference } from '$lib/preferences.svelte';

export async function requestNotifications(): Promise<void> {
  if (!window.isSecureContext || !('Notification' in window)) {
    toast.error('Desktop notifications require HTTPS or localhost and browser support.');
    return;
  }
  const permission = await Notification.requestPermission();
  setPreference('desktopNotifications', permission === 'granted');
  toast.info('Desktop notifications: ' + permission);
}

export function notify(message: string, desktop = false): void {
  if (preferences.successToasts) toast.success(message);
  if (desktop && preferences.desktopNotifications && window.isSecureContext && 'Notification' in window && Notification.permission === 'granted') {
    new Notification(message);
  }
}

