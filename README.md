# 🛰️ NodeWatch MCP (`nodewatch-mcp`)

**NodeWatch MCP** is a lightweight, cross-platform Model Context Protocol (MCP) server that empowers LLMs to monitor, inspect, and analyze system health and hardware telemetry in real time.

Designed for seamless deployment across developer workstations and production infrastructure, it supports dual transport modes: **STDIO** for local AI desktop clients (Claude Desktop, Cursor, VS Code) and **Streamable HTTP/SSE** for long-running remote server monitoring across AWS, Docker, or bare metal.

### 🚀 Highlights
- **📊 Deep Telemetry:** Real-time metrics for CPU load, RAM/Swap, disk I/O, network traffic, and top resource-consuming processes.
- **🔌 Dual-Transport Architecture:** Works out of the box locally via `stdio` (`uvx nodewatch-mcp`) or as a network daemon via `http`/`sse`.
- **⚡ Zero Setup Required:** Run instantly with `uvx` without manual cloning or dependency management.
- **🛡️ Cross-Platform:** Consistent telemetry parsing across Linux, macOS, and Windows.
