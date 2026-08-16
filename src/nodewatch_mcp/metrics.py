import datetime
import psutil
import socket
from typing import List
import time
from nodewatch_mcp.schemas import (
    CpuMetrics,
    DiskMetrics,
    DiskUsage,
    MemoryMetrics,
    MemoryUsage,
    NetworkInterfaceMetrics,
    NetworkMetrics,
    Process,
    SwapMemoryUsage,
    TopProcesses,
    SystemOverview
)

def get_cpu_metrics() -> CpuMetrics:
    """Gathers current CPU metrics."""
    return CpuMetrics(
        logical_cores=psutil.cpu_count(logical=True),
        physical_cores=psutil.cpu_count(logical=False),
        # Make one call for per-core usage and calculate total from it
        # interval=1 makes it a blocking call for 1 second to get accurate usage
        usage_per_core=(usage := psutil.cpu_percent(interval=1, percpu=True)),
        total_usage=sum(usage) / len(usage),
    )

def get_memory_metrics() -> MemoryMetrics:
    """Gathers current RAM and Swap memory metrics."""
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return MemoryMetrics(
        ram=MemoryUsage(**ram._asdict()),
        swap=SwapMemoryUsage(**swap._asdict()),
    )


def get_disk_metrics() -> DiskMetrics:
    """Gathers disk usage statistics for all partitions."""
    partitions = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append(
                DiskUsage(
                    device=part.device,
                    mountpoint=part.mountpoint,
                    fstype=part.fstype,
                    **usage._asdict(),
                )
            )
        except (FileNotFoundError, PermissionError):
            # Ignore partitions that are not accessible
            continue
    return DiskMetrics(partitions=partitions)

def get_network_metrics() -> NetworkMetrics:
    """Gathers network I/O statistics for all interfaces."""
    net_io = psutil.net_io_counters(pernic=True)
    interfaces = {
        name: NetworkInterfaceMetrics(**stats._asdict())
        for name, stats in net_io.items()
    }
    return NetworkMetrics(interfaces=interfaces)


def get_top_processes(count: int = 10) -> TopProcesses:
    """Gathers a list of the top resource-consuming processes."""
    # First pass: initialize CPU percent calculation timers for running processes
    for proc in psutil.process_iter(["cpu_percent"]):
        pass

    # Brief delay so psutil can calculate the CPU usage delta
    time.sleep(0.1)

    attrs = [
        "pid",
        "name",
        "username",
        "cpu_percent",
        "memory_percent",
        "status",
    ]
    processes: List[Process] = []

    for proc in psutil.process_iter(attrs):
        try:
            info = proc.info

            # Ensure clean float rounding and handle None values
            cpu = info.get("cpu_percent") or 0.0
            mem = info.get("memory_percent") or 0.0

            info["cpu_percent"] = round(float(cpu), 2)
            info["memory_percent"] = round(float(mem), 2)

            processes.append(Process(**info))
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    # Sort descending by CPU usage
    sorted_processes = sorted(
        processes, key=lambda p: p.cpu_percent, reverse=True
    )

    return TopProcesses(processes=sorted_processes[:count])


def get_system_overview() -> SystemOverview:
    """Gathers a high-level system overview."""
    boot_time_timestamp = psutil.boot_time()
    boot_dt = datetime.datetime.fromtimestamp(boot_time_timestamp, tz=datetime.timezone.utc)
    uptime_seconds = (datetime.datetime.now(datetime.timezone.utc).timestamp() - boot_time_timestamp)
    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "localhost"

    return SystemOverview(
        hostname=hostname,
        os=f"{psutil.os.uname().sysname} {psutil.os.uname().release}",
        uptime=uptime_str,
        boot_time=boot_dt,
    )