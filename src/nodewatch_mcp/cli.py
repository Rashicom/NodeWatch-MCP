import argparse
import os
import sys

from nodewatch_mcp import __version__
from nodewatch_mcp.server import mcp


def main() -> None:
    """CLI entrypoint for NodeWatch MCP Server."""
    parser = argparse.ArgumentParser(
        prog="nodewatch-mcp",
        description="NodeWatch MCP - Real-time system health and server metrics provider.",
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="Communication protocol to use (default: stdio). Supports env var MCP_TRANSPORT.",
    )

    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        help="Host address for HTTP/SSE transport (default: 0.0.0.0). Supports env var MCP_HOST.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8000")),
        help="Port number for HTTP/SSE transport (default: 8000). Supports env var MCP_PORT.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show package version and exit.",
    )

    args = parser.parse_args()

    # STDIO transport (Default for local LLM clients like Claude Desktop / Cursor)
    if args.transport == "stdio":
        # Do not print directly to stdout here; it corrupts JSON-RPC communication
        mcp.run(transport="stdio")

    # HTTP transport (For remote cloud / Docker microservice deployments)
    elif args.transport == "http":
        sys.stderr.write(
            f"Starting NodeWatch MCP in HTTP mode on {args.host}:{args.port}\n"
        )
        mcp.run(transport="http", host=args.host, port=args.port)

    # SSE transport
    elif args.transport == "sse":
        sys.stderr.write(
            f"Starting NodeWatch MCP in SSE mode on {args.host}:{args.port}\n"
        )
        mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()