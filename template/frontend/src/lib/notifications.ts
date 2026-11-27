import { toast } from 'svelte-sonner';

export async function requestNotifications(): Promise<void> {
  if (!window.isSecureContext || !('Notification' in window)) {
    toast.error('Desktop notifications require HTTPS or localhost and browser support.');
    return;
  }
  toast.info('Desktop notifications: ' + await Notification.requestPermission());
}

export function notify(message: string, desktop = false): void {
  toast.success(message);
  if (desktop && window.isSecureContext && 'Notification' in window && Notification.permission === 'granted') {
    new Notification(message);
  }
}

