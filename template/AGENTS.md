# Agent instructions

- Start with task doctor; run task setup when dependencies are missing. Use Task exclusively for project installation, building, testing, formatting, code generation, dependency changes and development operations. Run task --list to discover commands; add new tasks rather than inventing ad hoc command sequences.
- Python lives in app; Svelte 5 lives in frontend/src. Use runes and the vendored shadcn-svelte components. Add components through task ui:add.
- Use shared theme tokens, not component-specific colors. Keep Script → Markup → Style.
- Prefer maintained libraries and straightforward implementation. No gratuitous abstraction.
- Use typed FastAPI responses, parameterized SQL, shared Database and cached Settings.
- If MCP is enabled, REST and MCP share application services. Keep MCP tools read-only unless intentionally authorized.
- Add focused tests for meaningful changes; strict test-first sequencing is not required.
- Never expose ttyd, API or MCP publicly without appropriate access controls.
- Run checks and verify behavior before reporting completion.

- Reuse NoteForm, NotesTable and PaneForge rather than inventing form, table or resize behavior. Use TanStack Form with Zod for client validation and Pydantic for authoritative server validation.
- Use standalone Svelte 5 + Vite; do not add a second application backend.
- Diagnostics use psutil. Keep optional SSE and Taskiq dependencies/files conditional in Copier.
- Run task screenshots to verify visuals using a dedicated test database.

- After changing Python models or routes, run task api:generate. Use the generated components and paths through openapi-fetch; never duplicate API contracts or edit generated declarations.
- Run task fix and task check before committing. ESLint handles Svelte/TypeScript; Prettier owns formatting. Do not disable lint rules to pass CI.

- Add left-aligned semantic icons to command and context menu items, preserving visible labels and keyboard navigation. Use accessible switches with persistent settings. Keep SJSF conditional in Copier.

- Use TanStack Query for server state; define reusable query options in src/lib/queries.ts, invalidate relevant keys after mutations, and update the same cache from SSE. Keep local state for UI only.

- If RSS is enabled, publish only explicitly curated announcements using task rss:publish (or app.rss.publish inside application code); never automatically expose private application records. Use feedgenerator for XML generation and /feed.rss for discovery.

- Use the vendored shadcn-svelte Vega Sidebar, Dropdown Menu, Item, Kbd, Marker, Select, Separator, Switch and Tooltip components for consistent UI. Preserve accessible names, keyboard navigation, collapsed icon tooltips and mobile navigation.

- Reuse Navigation Menu, Pagination, Popover, Range Calendar and Scroll Area. Keep paging connected to TanStack Table; use real UTC creation dates for note filtering, preserving unknown dates in migrated records.

- Use typed operation-specific ApiError messages; do not expose server exception details to users. SSE sends revisions only; invalidate the notes query on reconnect and change. If ntfy is enabled, send only deliberate messages to the configured topic; never publish private records automatically.

- Keep App.svelte as composition only. Pages belong in frontend/src/pages; shell navigation, header and command palette in lib/shell; settings sections in lib/settings; domain UI and query coordination in lib/features. Add page metadata in lib/shell/navigation.ts and reuse PageNavigation and CommandPalette. Preserve conditional Copier features when moving files.
