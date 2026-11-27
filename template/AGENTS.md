# Agent instructions

- Start with task setup. Use task dev, task check, task test and task build.
- Python lives in app; Svelte 5 lives in frontend/src. Use runes and the vendored shadcn-svelte components. Add new components through the registry CLI.
- Use shared theme tokens, not component-specific colors. Keep Script → Markup → Style.
- Prefer maintained libraries and straightforward implementation. No gratuitous abstraction.
- Use typed FastAPI responses, parameterized SQL, shared Database and cached Settings.
- If MCP is enabled, REST and MCP share application services. Keep MCP tools read-only unless intentionally authorized.
- Add focused tests for meaningful changes; strict test-first sequencing is not required.
- Never expose ttyd, API or MCP publicly without appropriate access controls.
- Run checks and verify behavior before reporting completion.

- Reuse NoteForm, NotesTable and PaneForge rather than inventing form, table or resize behavior. Use Zod for client validation and Pydantic for authoritative server validation.
- SvelteKit is static SPA only; do not add a second application backend or server actions.
- Diagnostics use psutil. Keep optional SSE and Taskiq dependencies/files conditional in Copier.
- Run task screenshots to verify visuals using a dedicated test database.

- After changing Python models or routes, run task api:generate. Use the generated components and paths through openapi-fetch; never duplicate API contracts or edit generated declarations.
- Run task fix and task check before committing. ESLint handles Svelte/TypeScript; Prettier owns formatting. Do not disable lint rules to pass CI.
