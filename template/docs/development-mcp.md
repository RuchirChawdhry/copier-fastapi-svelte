# Development MCP

Always included for local development. It is independent of optional application MCP at /mcp/. FastMCP is a dev dependency in every profile, and a runtime dependency only when application MCP is enabled. The app wheel excludes tools; the sdist excludes development MCP source. Use `uv sync --locked --no-dev` for production. `task serve` launches the API with `--no-dev`; the normal development and test commands retain development dependencies.

## Setup and registration

After `task setup`, use `task mcp:dev:inspect` to list tool schemas and `task mcp:dev:check` to run focused tests. The agent starts the server as a stdio subprocess. Configure its working directory to the project root. Example client JSON (adjust absolute path):

```json
{
  "mcpServers": {
    "project-dev": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/project", "run", "--locked", "python", "-m", "tools.dev_mcp"]
    }
  }
}
```

The optional application server is registered separately as project-app with the Streamable HTTP URL http://127.0.0.1:8000/mcp/. Use your client's HTTP configuration syntax. Never mount the development server into FastAPI. Stdio protocol uses stdout exclusively; FastMCP logs go to stderr.

## Tools

| Category | Tools |
| --- | --- |
| Project | project_context, list_features, list_pages, list_components, git_status |
| Environment | doctor, service_status, dependency_status |
| API | list_endpoints, inspect_endpoint, check_api_contract |
| Browser | inspect_page, browser_diagnostics, browser_errors, inspect_network, capture_screenshot, accessibility_audit |
| Database | database_status, database_schema, database_indexes |
| Verification | run_checks, run_tests, test_results |

Examples: call project_context and doctor before implementation; inspect_endpoint(method="POST", path="/api/notes") before changing a request type; run_checks(scope="api") for focused backend checks. Start task dev before browser tools, then call browser_diagnostics(page="Overview"), accessibility_audit(page="Settings"), or capture_screenshot(page="Settings", theme="dark"). Browser tools open a fresh Chromium session on the fixed localhost development origin; page names select existing sidebar pages, not arbitrary URLs. They block non-GET/HEAD HTTP requests and external origins, and report a bounded snapshot of observed errors and requests. Screenshots return MCP image content and do not change repository showcase images.

run_tests(scope="backend") writes backend.xml; browser scope uses the existing prebuilt E2E task and requires free ports. test_results reads these reports, including timestamps; it does not retrieve GitHub logs. check_api_contract regenerates disposable OpenAPI JSON. Verification may write normal test/build artifacts; tools are not globally read-only. Database tools read schema only via SQLite read-only mode and reject paths outside the project. Browser output and test errors may contain application text; use development data, not secrets or production records. Redaction is best-effort. The MCP server is not a sandbox and runs with local user permissions. No arbitrary shell, SQL, or URL tool is exposed.
