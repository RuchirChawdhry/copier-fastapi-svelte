# Agent instructions

- Start with task setup. Use task dev, task check, task test and task build.
- Python lives in app; Svelte 5 lives in frontend/src. Use runes and the vendored shadcn-svelte components. Add new components through the registry CLI.
- Use shared theme tokens, not component-specific colors. Keep Script → Markup → Style.
- Prefer maintained libraries and straightforward implementation. No gratuitous abstraction.
- Use typed FastAPI responses, parameterized SQL, shared Database and cached Settings.
- REST and MCP share application services. Keep MCP tools read-only unless intentionally authorized.
- Add focused tests for meaningful changes; strict test-first sequencing is not required.
- Never expose ttyd, API or MCP publicly without appropriate access controls.
- Run checks and verify behavior before reporting completion.

- Reuse NoteForm, NotesTable and PaneForge rather than inventing form, table or resize behavior. Use Zod for client validation and Pydantic for authoritative server validation.
- SvelteKit is static SPA only; do not add a second application backend or server actions.
- Diagnostics use psutil. Keep optional SSE and Taskiq dependencies/files conditional in Copier.
- Run task screenshots to verify visuals using a dedicated test database.
