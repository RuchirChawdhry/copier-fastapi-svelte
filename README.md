# copier-fastapi-svelte

Agent-ready Copier starter: FastAPI, Svelte 5, TypeScript, Vite, Tailwind, shadcn-svelte, SQLite WAL, Caddy and optional FastMCP. Standalone Svelte 5 + Vite builds a static SPA; FastAPI is the only application backend.

```sh
uvx --from copier==9.14.1 copier copy gh:RuchirChawdhry/copier-fastapi-svelte my-app
cd my-app
task setup
task dev
```

Optional Taskiq/Redis, ttyd/xterm.js, live SSE, MCP, RSS announcements, ntfy push notifications and JSON Schema forms (SJSF) are off by default. Five themes, Ctrl+K and context menus with leading icons, persistent settings switches, browser notifications, TanStack Table, TanStack Query, PaneForge, Zod/TanStack Form and psutil diagnostics are standard.

See [screenshots](screenshots/) and the generated README and AGENTS.md.


API types are generated from FastAPI OpenAPI using task api:generate. ESLint, typescript-eslint, eslint-plugin-svelte, Prettier and svelte-check are integrated into task check and task fix.

See the [frontend benchmark](benchmarks/2026-11-27.md) for measured SvelteKit versus standalone Svelte build and startup performance. Re-run the Frontend benchmark workflow to collect fresh measurements.

Optional RSS publishing uses feedgenerator and exposes /feed.rss with automatic browser discovery and command-palette links. Announcements are explicitly published with task rss:publish, never derived from private notes.

Go Task is the development command interface, including template rendering, validation, screenshots and benchmarks. Run `task --list-all` in the template or generated project. GitHub Actions delegates development commands to the same Taskfiles.

Run `task doctor` or `task doctor:json` inside generated projects. The template preflight renders and lints seven pairwise configurations (including minimal and full); the same seven receive runtime validation. A coverage test verifies every pair of Boolean feature values.

## Versioned releases and dependency freezing

Use the latest published semantic version tag, or select an explicit tag:

```sh
uvx --from copier==9.14.1 copier copy --vcs-ref=v0.1.0 gh:RuchirChawdhry/copier-fastapi-svelte my-app
cd my-app
task setup
```

The example tag is available once the first release is published. The manually dispatched **Versioned Copier release** workflow creates a release-only commit containing 32 backend and two frontend lockfile profiles, validates the rendered locks and minimal/full applications, and publishes a semantic version tag only after success. It does not modify main. Each generated project receives just its matching uv.lock and frontend/pnpm-lock.yaml. Use `--vcs-ref=main` for unreleased development copies; `task deps:bootstrap` creates missing locks there before frozen installation. Commit both generated locks. Use `task deps:lock` or the dependency add/remove tasks for intentional changes; normal install and runtime commands reject stale Python locks and frozen pnpm install rejects stale frontend locks.

For updates, commit local work, then run `uvx --from copier==9.14.1 copier update --vcs-ref=v0.2.0` from the generated project (substitute a published tag). Inspect merge conflicts and lockfile changes, then run `task deps:check`, `task install` and `task check`.

CI caches the uv package cache, the pnpm content-addressed store, and Chromium binaries (keyed by installed Playwright version). Neither project environments nor generated lockfiles are cached. Screenshot scenarios are independent; target a single image with `task screenshots -- --grep 12-navigation-menu` in the generated app.

Showcase screenshots run against the actual frontend with deterministic Playwright API fixtures, not a live backend or database. Ordinary integration tests still exercise SQLite and FastAPI.
