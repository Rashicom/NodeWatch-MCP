# 🛰️ NodeWatch MCP (`nodewatch-mcp`)

**NodeWatch MCP** is a lightweight, cross-platform Model Context Protocol (MCP) server that empowers LLMs to monitor, inspect, and analyze system health and hardware telemetry in real time.

Designed for seamless deployment across developer workstations and production infrastructure, it supports multiple transport modes: **STDIO** for local AI desktop clients (e.g., Cursor, VS Code extensions) and **HTTP/SSE** for remote server monitoring.

### 🚀 Highlights
- **📊 Deep Telemetry:** Real-time metrics for CPU load, RAM/Swap, disk I/O, network traffic, and top resource-consuming processes.
- **🔌 Multi-Transport Architecture:** Works out of the box locally via `stdio` or as a network daemon via `http`/`sse`.
- **⚡ Zero Setup Required:** Run instantly with `uvx` without manual cloning or dependency management.
- **🛡️ Cross-Platform:** Consistent telemetry parsing across Linux, macOS, and Windows.
- **🤖 LLM Ready:** Provides a clear tool-use schema for easy integration with agents from Anthropic, Google, OpenAI, and more.

---

## 🛠️ Available Tools

NodeWatch MCP exposes the following functions for an LLM to call:

- **`system_overview()`**: Get high-level host metadata, OS platform, boot time, and system uptime.
- **`cpu_metrics()`**: Get current CPU metrics, including logical/physical core counts and usage.
- **`memory_metrics()`**: Get current RAM and Swap memory usage statistics.
- **`disk_metrics()`**: Get disk usage statistics for all mounted partitions.
- **`network_metrics()`**: Get network I/O statistics for all network interfaces.
- **`top_processes(count: int = 10)`**: Get a list of the top `N` resource-consuming processes, sorted by CPU usage.

## ⚙️ Usage

The easiest way to run NodeWatch MCP is with `uvx`, which requires no installation.

### Local Mode (STDIO)

This is the default mode, ideal for local AI development tools that can communicate over standard input/output.

```bash
uvx nodewatch-mcp
```

### Network Mode (HTTP)

Run as a persistent server to allow remote LLM agents to monitor a machine.

```bash
uvx nodewatch-mcp --transport http --host 0.0.0.0 --port 8000
```

You can also configure this with environment variables:
```bash
export MCP_TRANSPORT=http
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
uvx nodewatch-mcp
```

## 🔗 Connecting to LLMs

NodeWatch MCP follows the Model Context Protocol (MCP) standard, making it compatible with various LLM tool-use interfaces.

### Connecting to Claude

Many Anthropic-compatible clients (like the official VS Code extension) can automatically manage MCP server processes. You can configure them to launch `nodewatch-mcp` directly.

1.  **For local use (recommended)**: Find the path to your `uvx` executable by running `which uvx` in your terminal. Then, in your client's settings (e.g., `settings.json` in VS Code), add a configuration for `nodewatch-mcp`.

    ```json
    {
      "mcp.servers": {
        "nodewatch": {
          "command": "/path/to/your/uvx",
          "args": [
            "nodewatch-mcp"
          ]
        }
      }
    }
    ```
    *Replace `/path/to/your/uvx` with the actual path from `which uvx`.* The client will now automatically start and communicate with `nodewatch-mcp` over `stdio`, which is the default transport.

2.  **For remote use**: Run the server in HTTP mode on your target machine. Then, in your agent's code, you can make POST requests to the server's endpoint (e.g., `http://<your-server-ip>:8000/mcp`) with the appropriate JSON-RPC payload to call a tool.

### Connecting to Gemini CLI or API

To use NodeWatch with Google's Gemini models, you'll need a small shim or proxy that translates Gemini's tool-calling format into MCP's JSON-RPC format.

1.  Run NodeWatch MCP in HTTP mode:
    ```bash
    uvx nodewatch-mcp --transport http
    ```
2.  When defining tools for your Gemini API call, you would create function declarations that match the tools listed above.
3.  Your application code would catch the `functionCall` from Gemini's response, execute an HTTP POST request to the NodeWatch server (e.g., `http://127.0.0.1:8000/mcp`), and return the result back to the Gemini model to continue the conversation.

This setup allows Gemini to query the state of the machine where NodeWatch is running.
