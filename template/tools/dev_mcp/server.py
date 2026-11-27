from fastmcp import FastMCP

from .browser import (
    accessibility_audit,
    browser_diagnostics,
    browser_errors,
    capture_screenshot,
    inspect_network,
    inspect_page,
)
from .database import database_indexes, database_schema, database_status
from .environment import dependency_status, doctor, git_status, service_status
from .project import (
    inspect_endpoint,
    list_components,
    list_endpoints,
    list_features,
    list_pages,
    project_context,
)
from .verification import check_api_contract, run_checks, run_tests, test_results


def create_server() -> FastMCP:
    server = FastMCP(
        project_context()["name"] + "-dev",
        instructions="Local development tooling only. Use doctor and project_context first. "
        "Browser tools require task dev. Verification commands are explicitly allowlisted. "
        "Do not use this server with production or sensitive data.",
    )
    for tool in (
        project_context, list_features, list_pages, list_components,
        doctor, service_status, dependency_status, git_status,
        list_endpoints, inspect_endpoint, check_api_contract,
        inspect_page, browser_diagnostics, browser_errors, inspect_network,
        capture_screenshot, accessibility_audit,
        database_schema, database_status, database_indexes,
        run_checks, run_tests, test_results,
    ):
        server.tool(tool)
    return server
