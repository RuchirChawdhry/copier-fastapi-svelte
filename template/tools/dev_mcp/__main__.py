import argparse
import asyncio
import json

from fastmcp import Client

from .server import create_server


async def inspect(server):
    async with Client(server) as client:
        tools = await client.list_tools()
        print(json.dumps([tool.model_dump(mode="json") for tool in tools], indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()
    server = create_server()
    if args.inspect:
        asyncio.run(inspect(server))
    else:
        server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
