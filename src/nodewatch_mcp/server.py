from fastmcp import Context, FastMCP

from nodewatch_mcp.metrics import (
    get_cpu_metrics,
    get_disk_metrics,
    get_log_records,
    get_memory_metrics,
    get_network_metrics,
    get_open_ports,
    get_process_by_port,
    get_system_overview,
    get_top_processes,
    kill_process,
    list_log_files,
)
from nodewatch_mcp.schemas import (
    CpuMetrics,
    DiskMetrics,
    LogFiles,
    LogRecords,
    MemoryMetrics,
    NetworkMetrics,
    OpenPort,
    Process,
    SystemOverview,
    TopProcesses,
)

mcp = FastMCP(
    name="🛰️ NodeWatch MCP",
    instructions="A server for monitoring system health and hardware telemetry.",
    version="0.1.0",
)


@mcp.tool()
def system_overview() -> SystemOverview:
    """Get high-level host metadata, OS platform, boot time, and system uptime."""
    return get_system_overview()


@mcp.tool()
def cpu_metrics() -> CpuMetrics:
    """
    Get current CPU metrics.

    Provides details on logical and physical cores, per-core usage, and total CPU usage.
    Note: This is a blocking call for 1 second to get an accurate usage reading.
    """
    return get_cpu_metrics()


@mcp.tool()
def memory_metrics() -> MemoryMetrics:
    """Get current RAM and Swap memory metrics."""
    return get_memory_metrics()


@mcp.tool()
def disk_metrics() -> DiskMetrics:
    """Get disk usage statistics for all mounted partitions."""
    return get_disk_metrics()


@mcp.tool()
def network_metrics() -> NetworkMetrics:
    """Get network I/O statistics for all network interfaces."""
    return get_network_metrics()


@mcp.tool()
def top_processes(count: int | None = 10) -> TopProcesses:
    """Get a list of the top resource-consuming processes, sorted by CPU usage."""
    return get_top_processes(count=count)


@mcp.tool()
def log_files() -> LogFiles | str:
    """Get a list of available log files on the system."""
    try:
        return list_log_files()
    except Exception as e:  # noqa: BLE001
        return f"Error: {e!s}"


@mcp.tool()
def log_records(filename: str, num_records: int = 100) -> LogRecords | str:
    """Get a specific number of records from a given log file."""
    try:
        return get_log_records(filename, num_records)
    except FileNotFoundError as e:
        return f"Error: File not found. {e!s}"
    except PermissionError as e:
        return f"Error: Permission denied. {e!s}"
    except Exception as e:  # noqa: BLE001
        return f"Error: {e!s}"


@mcp.tool()
def open_ports() -> list[OpenPort] | str:
    """Get a list of all open ports and their associated processes."""
    try:
        return get_open_ports()
    except Exception as e:  # noqa: BLE001
        return f"Error: {e!s}"


@mcp.tool()
def process_by_port(port: int) -> Process | str:
    """Get details of the process running on a specific port."""
    try:
        proc = get_process_by_port(port)
        if proc:
            return proc
        return f"No process found running on port {port}."
    except Exception as e:  # noqa: BLE001
        return f"Error: {e!s}"


@mcp.tool()
async def kill_process_on_port(port: int, context: Context) -> str:
    """Kill a process running on a specific port, after obtaining user confirmation."""
    try:
        proc = get_process_by_port(port)
        if not proc:
            return f"No process found running on port {port}."

        prompt = (
            f"You are a system administrator assistant. A user wants to kill the process "
            f"running on port {port}. The process is '{proc.name}' (PID: {proc.pid}). "
            "Write a short, direct 1-sentence warning/confirmation message "
            "evaluating the importance of this process. "
            "For example: 'This port is important to run Google Chrome, if you kill this your Chrome capability is lost. Do you want to kill the process?' "
            "Or 'There is a web server running on port 8000, do you want to kill it?'."
        )

        await context.info("Generating confirmation message...")
        sample_result = await context.sample(prompt, max_tokens=150)

        if (
            hasattr(sample_result, "content")
            and isinstance(sample_result.content, list)
            and len(sample_result.content) > 0
        ):
            confirmation_msg = getattr(
                sample_result.content[0], "text", str(sample_result)
            )
        else:
            confirmation_msg = getattr(sample_result, "value", str(sample_result))

        await context.info("Sending confirmation message to user...")
        elicit_result = await context.elicit(confirmation_msg)
        user_response = (
            str(getattr(elicit_result, "value", elicit_result)).lower().strip()
        )

        if user_response in ["yes", "y", "true", "proceed", "kill"]:
            success = kill_process(proc.pid)
            if success:
                return f"Successfully killed process '{proc.name}' (PID: {proc.pid}) on port {port}."
            else:
                return f"Failed to kill process '{proc.name}' (PID: {proc.pid}). Permission denied or process not found."
        else:
            return "Kill process aborted by user."
    except Exception as e:  # noqa: BLE001
        return f"Error: {e!s}"
