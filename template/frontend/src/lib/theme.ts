export const themes = [
  { id: 'dark', label: 'Dark' },
  { id: 'light', label: 'Light' },
  { id: 'oled', label: 'OLED' },
  { id: 'solarized-light', label: 'Solarized Light (Warm)' },
  { id: 'solarized-dark', label: 'Solarized Dark' },
] as const;
export type Theme = (typeof themes)[number]['id'];

export function currentTheme(): Theme {
  return themes.find((theme) => theme.id === document.documentElement.dataset.theme)?.id ?? 'dark';
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  document.documentElement.classList.toggle('dark', !['light', 'solarized-light'].includes(theme));
  localStorage.setItem('theme', theme);
}

