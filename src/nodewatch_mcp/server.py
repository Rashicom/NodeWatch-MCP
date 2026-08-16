from fastmcp import FastMCP

from nodewatch_mcp.metrics import (
    get_cpu_metrics,
    get_disk_metrics,
    get_memory_metrics,
    get_network_metrics,
    get_system_overview,
    get_top_processes,
)
from nodewatch_mcp.schemas import (
    CpuMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
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
