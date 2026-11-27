# copier-fastapi-svelte

Agent-ready Copier starter: FastAPI, Svelte 5, TypeScript, Vite, Tailwind, shadcn-svelte, SQLite WAL, Caddy and optional FastMCP. Standalone Svelte 5 + Vite builds a static SPA; FastAPI is the only application backend.

```sh
uvx --from copier copier copy gh:RuchirChawdhry/copier-fastapi-svelte my-app
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

Run `task doctor` or `task doctor:json` inside generated projects. The template preflight renders and lints every feature combination before the full validation matrix.
