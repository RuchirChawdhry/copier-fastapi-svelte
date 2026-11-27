import LayoutDashboard from '@lucide/svelte/icons/layout-dashboard';
import Settings from '@lucide/svelte/icons/settings';
import Activity from '@lucide/svelte/icons/activity';

export const pages = [
  { id: 'workspace', label: 'Overview', icon: LayoutDashboard, command: 'Open overview' },
  { id: 'settings', label: 'Settings', icon: Settings, command: 'Open settings' },
  { id: 'diagnostics', label: 'Diagnostics', icon: Activity, command: 'Open diagnostics' },
] as const;

export type Page = (typeof pages)[number]['id'];

export const pageLabels = {
  workspace: 'Overview',
  settings: 'Settings',
  diagnostics: 'Diagnostics',
} satisfies Record<Page, string>;
