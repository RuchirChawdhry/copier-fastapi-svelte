import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import svelte from 'eslint-plugin-svelte';
import prettier from 'eslint-config-prettier';
import globals from 'globals';
import svelteConfig from './svelte.config.js';

export default [
  {
    ignores: ['dist/**', '.svelte-kit/**', 'node_modules/**', 'test-results/**', 'playwright-report/**', 'src/lib/generated/**', 'src/lib/components/ui/**'],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...svelte.configs['flat/recommended'],
  {
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },
  {
    files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
    languageOptions: { parserOptions: { parser: tseslint.parser, svelteConfig } },
  },
  prettier,
  ...svelte.configs['flat/prettier'],
];
