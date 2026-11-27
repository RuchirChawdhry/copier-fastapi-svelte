# Development MCP

Always included, local stdio, FastMCP 4.2.6, separate from the optional application MCP at /mcp/. It is a development dependency and is excluded from the application wheel. Use `uv sync --locked --no-dev` for production.

After `task setup`, run `task mcp:dev:inspect` to discover tool schemas and `task mcp:dev:check` for focused tests. Configure the client to run the following command from the project root:

```sh
uv run --locked python -m tools.dev_mcp
```

## Tools

| Category | Tools |
| --- | --- |
| Project | project_context, list_pages, list_components, git_status |
| Environment | doctor, service_status, dependency_status |
| API | list_endpoints, inspect_endpoint, check_api_contract |
| Database | database_status, database_schema |
| Verification | run_checks, run_tests, test_results |

Browser inspection is intentionally not provided: use the agent's browser integration. Playwright remains the project test and showcase screenshot runner.

Project context discovers manifest versions, actual Task inventory and existing paths. Page metadata reads the navigation registry; component metadata uses the Svelte and TypeScript parsers. API inspection obtains a fresh OpenAPI snapshot, with source locations and candidate frontend/test references. Database tools use read-only workspace-local SQLite access; counts and integrity checks are opt-in. Verification uses allowlisted project tasks and JUnit reports, not arbitrary shell commands. Outputs can contain development paths and test text; do not run against production data.

## Examples

- `list_components(search="dropdown", category="ui")` — prop declarations and static import candidates.
- `check_api_contract()` — compares fresh generated TypeScript signatures without replacing existing files.
- `database_status(count_rows=true, integrity="quick")` — optional scans; `database_schema(table="notes")` includes indexes, foreign keys and DDL.
- `run_checks(scope="ruff")`, `run_checks(scope="svelte")`, `run_checks(scope="contract")` — focused checks.
- `run_tests(scope="backend", files=["tests/test_dev_mcp.py"], match="contract")` or `run_tests(scope="browser", match="settings")`; `failed_only=true` uses native last-failure selection. Browser tests require built assets and available ports.
- `test_results()` reports latest JUnit artifacts, failure details, durations and source-mtime freshness (not a commit-level guarantee).

Service configuration discovers the template's literal Vite/Caddy settings and Pydantic database/Redis settings when installed; computed custom Vite/Caddy configuration and OS-restricted process ownership may require manual inspection. Dependency status compares direct manifest/lock/install data and delegates full lock validation to uv and pnpm. Static reference matches are candidates, not a complete call graph. No new Copier options.
