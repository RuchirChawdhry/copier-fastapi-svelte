# copier-fastapi-svelte

Agent-ready Copier starter: FastAPI, Svelte 5, TypeScript, Vite, Tailwind, shadcn-svelte, SQLite WAL, Caddy and optional FastMCP. SvelteKit builds a static client-only SPA for Formsnap/Superforms compatibility; FastAPI is the only application backend.

```sh
uvx --from copier copier copy gh:RuchirChawdhry/copier-fastapi-svelte my-app
cd my-app
task setup
task dev
```

Optional Taskiq/Redis, ttyd/xterm.js, live SSE and MCP are off by default. Five themes, Ctrl+K, context menus, browser notifications, TanStack Table, PaneForge, Zod/Formsnap and psutil diagnostics are standard.

See [screenshots](screenshots/) and the generated README and AGENTS.md.


API types are generated from FastAPI OpenAPI using task api:generate. ESLint, typescript-eslint, eslint-plugin-svelte, Prettier and svelte-check are integrated into task check and task fix.
