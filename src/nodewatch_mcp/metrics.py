import datetime
import os
import socket
import sys
import time
from collections import deque
from pathlib import Path

import psutil

from nodewatch_mcp.schemas import (
    CpuMetrics,
    DiskMetrics,
    DiskUsage,
    LogFiles,
    LogRecords,
    MemoryMetrics,
    MemoryUsage,
    NetworkInterfaceMetrics,
    NetworkMetrics,
    OpenPort,
    Process,
    SwapMemoryUsage,
    SystemOverview,
    TopProcesses,
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
    processes: list[Process] = []

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
    sorted_processes = sorted(processes, key=lambda p: p.cpu_percent, reverse=True)

    return TopProcesses(processes=sorted_processes[:count])


def get_system_overview() -> SystemOverview:
    """Gathers a high-level system overview."""
    boot_time_timestamp = psutil.boot_time()
    boot_dt = datetime.datetime.fromtimestamp(boot_time_timestamp, tz=datetime.UTC)
    uptime_seconds = (
        datetime.datetime.now(datetime.UTC).timestamp() - boot_time_timestamp
    )
    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

    try:
        hostname = socket.gethostname()
    except OSError:
        hostname = "localhost"

    return SystemOverview(
        hostname=hostname,
        os=f"{psutil.os.uname().sysname} {psutil.os.uname().release}",
        uptime=uptime_str,
        boot_time=boot_dt,
    )


def list_log_files() -> LogFiles:
    """Retrieves a list of log filenames from the system log directory."""
    if sys.platform == "win32":
        log_dir = (
            Path(os.environ.get("WINDIR", "C:\\Windows"))
            / "System32"
            / "winevt"
            / "Logs"
        )
    else:
        log_dir = Path("/var/log")

    files = []
    if log_dir.exists() and log_dir.is_dir():
        for path in log_dir.rglob("*"):
            if path.is_file():
                files.append(path.name)

    return LogFiles(files=files)


def get_log_records(filename: str, num_records: int) -> LogRecords:
    """Retrieves a specific number of records from a given log file."""
    if sys.platform == "win32":
        log_dir = (
            Path(os.environ.get("WINDIR", "C:\\Windows"))
            / "System32"
            / "winevt"
            / "Logs"
        )
    else:
        log_dir = Path("/var/log")

    records = []
    file_path = None

    if log_dir.exists() and log_dir.is_dir():
        for path in log_dir.rglob("*"):
            if path.name == filename and path.is_file():
                file_path = path
                break

    if not file_path:
        raise FileNotFoundError(f"Log file '{filename}' not found in {log_dir}")

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            records = [line.strip() for line in deque(f, maxlen=num_records)]
    except PermissionError:
        raise PermissionError(f"Permission denied when trying to read {file_path}")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Failed to read {file_path}: {e!s}")

    return LogRecords(records=records)


def get_open_ports() -> list[OpenPort]:
    """Retrieves all ports currently open/listening and their associated processes."""
    ports = []

    connections_with_pid = []
    try:
        for conn in psutil.net_connections(kind="all"):
            connections_with_pid.append((conn, getattr(conn, "pid", None)))
    except psutil.AccessDenied:
        for proc in psutil.process_iter(["pid"]):
            try:
                for conn in proc.net_connections(kind="all"):
                    connections_with_pid.append((conn, proc.info["pid"]))
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    for conn, pid in connections_with_pid:
        if not conn.laddr or not hasattr(conn.laddr, "port"):
            continue

        port = conn.laddr.port
        if not port:
            continue

        protocol = (
            "tcp"
            if conn.type == socket.SOCK_STREAM
            else "udp"
            if conn.type == socket.SOCK_DGRAM
            else "other"
        )

        process_name = None
        if pid:
            try:
                proc = psutil.Process(pid)
                process_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        ports.append(
            OpenPort(
                port=port,
                protocol=protocol,
                status=conn.status,
                pid=pid,
                process_name=process_name,
            )
        )

    return ports


def get_process_by_port(port: int) -> Process | None:
    """Retrieves the process running on a specific port."""
    connections_with_pid = []
    try:
        for conn in psutil.net_connections(kind="all"):
            connections_with_pid.append((conn, getattr(conn, "pid", None)))
    except psutil.AccessDenied:
        for proc in psutil.process_iter(["pid"]):
            try:
                for conn in proc.net_connections(kind="all"):
                    connections_with_pid.append((conn, proc.info["pid"]))
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    for conn, pid in connections_with_pid:
        if (
            conn.laddr
            and hasattr(conn.laddr, "port")
            and conn.laddr.port == port
            and pid
        ):
            try:
                proc = psutil.Process(pid)
                info = proc.as_dict(
                    attrs=[
                        "pid",
                        "name",
                        "username",
                        "cpu_percent",
                        "memory_percent",
                        "status",
                    ]
                )
                info["cpu_percent"] = round(float(info.get("cpu_percent") or 0.0), 2)
                info["memory_percent"] = round(
                    float(info.get("memory_percent") or 0.0), 2
                )
                return Process(**info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    return None


def kill_process(pid: int) -> bool:
    """Kills the process with the given PID."""
    try:
        proc = psutil.Process(pid)
        proc.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
