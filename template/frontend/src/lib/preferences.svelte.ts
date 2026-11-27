const defaults = {
  successToasts: true,
  desktopNotifications: false,
  reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
};

export const preferences = $state({
  ...defaults,
  ...JSON.parse(localStorage.getItem('workspace-preferences') ?? '{}') as Partial<typeof defaults>,
});

export function setPreference<K extends keyof typeof defaults>(key: K, value: (typeof defaults)[K]): void {
  preferences[key] = value;
  localStorage.setItem('workspace-preferences', JSON.stringify(preferences));
  document.documentElement.toggleAttribute('data-reduced-motion', preferences.reducedMotion);
}

document.documentElement.toggleAttribute('data-reduced-motion', preferences.reducedMotion);
