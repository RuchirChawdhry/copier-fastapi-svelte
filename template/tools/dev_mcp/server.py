from fastmcp import FastMCP

from .database import database_schema, database_status
from .environment import dependency_status, doctor, git_status, service_status
from .project import (
    inspect_endpoint,
    list_components,
    list_endpoints,
    list_pages,
    project_context,
)
from .verification import check_api_contract, run_checks, run_tests, test_results


def create_server() -> FastMCP:
    server = FastMCP(
        project_context()["name"] + "-dev",
        instructions="Project-specific local development intelligence. Use project_context and doctor "
        "first. Use your own browser tools for UI inspection. Verification runs existing project tasks.",
    )
    for tag, tools in (
        ("project", (project_context, list_pages, list_components, git_status)),
        ("environment", (doctor, service_status, dependency_status)),
        ("api", (list_endpoints, inspect_endpoint, check_api_contract)),
        ("database", (database_schema, database_status)),
        ("verification", (run_checks, run_tests, test_results)),
    ):
        for tool in tools:
            server.tool(tool, tags={tag})
    return server
